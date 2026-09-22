#!/usr/bin/env python3
"""Verify one bounded track bucket -> PM4 packet -> backend draw capture."""

import argparse
import collections
import json
import re
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (.*?) (\{.*\})")
SECOND_TARGETS = {
    0x82417BC0: "procedural_models",
    0x823FDE50: "procedural_animated_scene",
    0x8245AB88: "procedural_characters",
    0x824136F0: "procedural_vegetation",
}


def verify(path: Path, source_frame: int, backend_frame: int,
           first_model_vtable: int | None = None) -> dict:
    events = collections.defaultdict(list)
    active_views = collections.defaultdict(list)
    for line in path.open(encoding="utf-8-sig", errors="replace"):
        match = EVENT.search(line)
        if match:
            thread, kind = int(match[1]), match[2]
            row = json.loads(match[3])
            if row["frame"] in (source_frame, backend_frame):
                events[kind].append((thread, row))
                if row["frame"] == source_frame:
                    if kind == "view begin":
                        active_views[thread].append(row["view"])
                    elif kind == "view end":
                        assert active_views[thread].pop() == row["view"]
                    elif kind == "track bucket entry":
                        assert active_views[thread][-1] == row["view"]
                    elif kind == "procedural item":
                        row["_inside_view"] = bool(active_views[thread])
    assert all(not stack for stack in active_views.values()), "view scope is unfinished"

    entries = [(thread, row) for thread, row in events["track bucket entry"]
               if row["frame"] == source_frame]
    summaries = [row for _, row in events["summary"]
                 if row["frame"] == source_frame]
    assert len(summaries) == 1 and entries, "source capture is incomplete"
    summary = summaries[0]
    assert summary["track_bucket_entries"] == len(entries) < summary["scope_limit"]
    assert not summary["unfinished_track_bucket_scopes"]
    assert not summary["unmatched_track_bucket_exits"]
    assert [row["ordinal"] for _, row in entries] == list(range(1, len(entries) + 1))

    views = {row["view"] for _, row in entries}
    presenters = {row["presenter"] for _, row in entries}
    assert len(views) == len(presenters) == 1, "multiple view/presenter identities"
    view, presenter = next(iter(views)), next(iter(presenters))
    slots = [row for _, row in events["track presentation"]
             if row["frame"] == source_frame and row["slot"] == 75]
    assert slots and all(row["receiver"] == presenter and row["arg9"] == view
                         for row in slots), "slot-75 relationship differs"
    bucket_indices = {5 * row["arg5"] + row["arg6"] for row in slots}

    packets = {}
    for kind in ("semantic packet", "direct packet"):
        packets[kind] = {(thread, row["ordinal"]): row
                         for thread, row in events[kind]
                         if row["frame"] == source_frame}
    prepared = [(thread, row) for thread, row in events["prepared draw"]
                if row["frame"] == backend_frame]
    draws = collections.Counter(row["packet_physical"]
                                for _, row in prepared)
    prepared_by_header = collections.defaultdict(list)
    for thread, row in prepared:
        prepared_by_header[row["packet_physical"]].append((thread, row))
    vertex_fetches = [(thread, row) for thread, row in events["prepared vertex fetch"]
                      if row["frame"] == backend_frame]
    fetch_signature_by_draw = {}
    fetch_origin_counts = collections.Counter()
    if vertex_fetches:
        fetches_by_draw = collections.defaultdict(list)
        for thread, row in vertex_fetches:
            fetches_by_draw[thread, row["draw"]].append(row)
        assert sum(row["vertex_fetch_count"] for _, row in prepared) == len(vertex_fetches)
        for thread, row in prepared:
            fetches = fetches_by_draw.pop((thread, row["ordinal"]), [])
            assert len(fetches) == row["vertex_fetch_count"]
            assert [fetch["slot"] for fetch in fetches] == list(range(len(fetches)))
            assert all(fetch["packet_physical"] == row["packet_physical"]
                       for fetch in fetches)
            for fetch in fetches:
                if "source_packet_0" not in fetch:
                    continue
                assert fetch["source_packet_0"] == fetch["source_packet_1"] != 0
                assert fetch["source_execution_0"] == fetch["source_execution_1"] != 0
                fetch_origin_counts["observed"] += 1
                if fetch["source_execution_0"] == row["indirect_execution"]:
                    assert (row["command_buffer"] <= fetch["source_packet_0"] <
                            row["packet_physical"])
                    fetch_origin_counts["same_execution"] += 1
                else:
                    fetch_origin_counts["carried_from_prior_execution"] += 1
            fetch_signature_by_draw[thread, row["ordinal"]] = tuple(
                (fetch["fetch_constant"], fetch["guest_base"], fetch["length"],
                 fetch["stride_words"], fetch["type"]) for fetch in fetches)
        assert not fetches_by_draw
    draw_index_counts = collections.defaultdict(set)
    for _, row in events["prepared draw"]:
        if row["frame"] == backend_frame:
            draw_index_counts[row["packet_physical"]].add(row["index_count"])
    assert draws, "backend draw capture is missing"

    claimed = set()
    physical_headers = set()
    bucket_by_semantic = {}
    counts = collections.Counter()
    first_fetch_signatures = set()
    for thread, row in entries:
        assert row["bucket"] == presenter + 56808 + 16 * (
            (row["bucket"] - presenter - 56808) // 16)
        assert (row["bucket"] - presenter - 56808) // 16 in bucket_indices
        first = bool(row["record"])
        assert first != bool(row["secondary_seen"]), "record path is ambiguous"
        assert first or row["secondary_record"], "selected record is null"
        path_name = "first" if first else "second"
        counts[path_name + "_entries"] += 1
        if first_model_vtable is not None:
            if first:
                assert row["first_object"] and row["first_vtable"] == first_model_vtable
                assert row["first_guard"] in (0, 1)
                counts["first_guard_passed"] += row["first_guard"] == 1
            else:
                assert row["secondary_resolved_seen"] and row["auxiliary_seen"]
                counts["second_resolved"] += bool(row["secondary_resolved"])
                counts["second_auxiliary_records"] += bool(row["auxiliary_record"])
        produced = 0
        for kind, label in (("semantic packet", "semantic"),
                            ("direct packet", "direct")):
            start, end = row["first_" + label], row["last_" + label]
            assert end >= start - 1, "invalid packet range"
            for ordinal in range(start, end + 1):
                key = (kind, thread, ordinal)
                assert key not in claimed, "packet belongs to multiple entries"
                claimed.add(key)
                packet = packets[kind].get((thread, ordinal))
                assert packet is not None, "packet ordinal is missing"
                if kind == "semantic packet":
                    bucket_by_semantic[(thread, ordinal)] = row
                physical_headers.add(packet["header_physical"])
                callbacks = draws[packet["header_physical"]]
                assert callbacks, "record packet has no backend draw"
                if first and fetch_signature_by_draw:
                    backend_draws = prepared_by_header[packet["header_physical"]]
                    signatures = {fetch_signature_by_draw[draw_thread, draw["ordinal"]]
                                  for draw_thread, draw in backend_draws}
                    assert len(signatures) == 1
                    signature = next(iter(signatures))
                    assert len(signature) == 1 and signature[0][0] == 95
                    assert signature[0][1] and signature[0][2]
                    assert all(draw["index_buffer_type"] == 0 and
                               draw["guest_primitive_type"] == 13
                               for _, draw in backend_draws)
                    first_fetch_signatures.add(signature)
                counts[path_name + "_packets"] += 1
                counts[path_name + "_draw_callbacks"] += callbacks
                produced += 1
        counts[path_name + "_producing_entries"] += bool(produced)
    assert len(physical_headers) == len(claimed), "packet header address reused"
    if first_fetch_signatures:
        counts["first_vertex_fetch_signatures"] = len(first_fetch_signatures)

    descriptor_bases = {}
    descriptor_kinds = collections.Counter()
    first_models_with_items = set()
    for thread, item in events["procedural item"]:
        if item["frame"] != source_frame or not item["submit_seen"]:
            continue
        assert item["first_semantic_packet"] == item["last_semantic_packet"]
        bucket = bucket_by_semantic.get((thread, item["first_semantic_packet"]))
        if bucket is None:
            counts["submitted_items_outside_buckets"] += 1
            counts["submitted_items_inside_view_unmatched"] += item["_inside_view"]
            continue
        assert item["descriptor_seen"] and item["runtime_seen"]
        path_name = "first" if bucket["record"] else "second"
        counts[path_name + "_submitted_items"] += 1
        descriptor_kinds[(path_name, item["descriptor_kind"])] += 1
        packet = packets["semantic packet"][(thread, item["first_semantic_packet"])]
        assert draw_index_counts[packet["header_physical"]] == {
            4 * item["submit_arg6"]}, "item count differs from backend draw"
        bases = (item["descriptor_address"] - 92 * item["descriptor_index"],
                 item["runtime_address"] - 68 * item["descriptor_index"])
        receiver = item["receiver"]
        assert receiver not in descriptor_bases or descriptor_bases[receiver] == bases
        descriptor_bases[receiver] = bases
        if path_name == "first" and "first_object" in bucket:
            first_models_with_items.add(bucket["first_object"])
    if first_model_vtable is not None:
        assert counts["first_submitted_items"] == counts["first_packets"]
        assert not counts["second_submitted_items"]
        assert not counts["submitted_items_inside_view_unmatched"]

    nodes = [(thread, row) for thread, row in events["item node"]
             if row["frame"] == source_frame]
    if nodes:
        assert summary["item_nodes"] == len(nodes) < summary["scope_limit"]
        assert not summary["unfinished_item_node_scopes"]
        assert not summary["unmatched_item_node_exits"]
        assert [row["ordinal"] for _, row in nodes] == list(range(1, len(nodes) + 1))
        items = {(thread, row["call"]): row
                 for thread, row in events["procedural item"]
                 if row["frame"] == source_frame}
        assert len(items) == len(nodes), "item call has no linked node"
        buckets = {(thread, row["ordinal"]): row for thread, row in entries}
        view_calls = {(thread, row["call"]): row
                      for thread, row in events["view begin"]
                      if row["frame"] == source_frame}
        claimed_items = set()
        for thread, node in nodes:
            assert node["node"] and node["list_head"]
            assert node["first_item"] == node["last_item"]
            key = (thread, node["first_item"])
            assert key not in claimed_items and key in items
            claimed_items.add(key)
            item = items[key]
            assert item["receiver"] == node["receiver"]
            assert item["descriptor_seen"] and item["runtime_seen"]
            assert item["descriptor_index"] == node["index"]
            bases = (item["descriptor_address"] - 92 * node["index"],
                     item["runtime_address"] - 68 * node["index"])
            receiver = item["receiver"]
            assert receiver not in descriptor_bases or descriptor_bases[receiver] == bases
            descriptor_bases[receiver] = bases
            assert (item["first_semantic_packet"], item["last_semantic_packet"]) == (
                node["first_semantic"], node["last_semantic"])
            if node["bucket_entry"]:
                bucket = buckets[(thread, node["bucket_entry"])]
                assert node["view_call"] and bucket["record"]
                assert view_calls[(thread, node["view_call"])]["view"] == bucket["view"]
                assert bucket["first_semantic"] <= node["first_semantic"]
                assert node["last_semantic"] <= bucket["last_semantic"]
                if item["submit_seen"]:
                    assert bucket_by_semantic[(thread, node["first_semantic"])] is bucket
                counts["first_item_nodes"] += 1
                counts["first_item_nodes_without_packet"] += not item["submit_seen"]
            else:
                assert not node["view_call"]
                counts["item_nodes_outside_view"] += 1
            assert item["submit_seen"] == (
                node["first_semantic"] == node["last_semantic"])
        assert claimed_items == set(items)

    candidates = [(thread, row) for thread, row in events["resource candidate"]
                  if row["frame"] == source_frame]
    if candidates:
        items = {(thread, row["call"]): row
                 for thread, row in events["procedural item"]
                 if row["frame"] == source_frame}
        candidate_slots = collections.defaultdict(set)
        resource_keys = set()
        for thread, candidate in candidates:
            key = (thread, candidate["call"])
            assert key in items
            item = items[key]
            assert item["submit_seen"]
            assert candidate["descriptor"] == item["descriptor_address"]
            assert candidate["slot"] in (0, 1)
            assert candidate["slot"] not in candidate_slots[key]
            candidate_slots[key].add(candidate["slot"])
            resource_keys.add(candidate["key"])
        assert set(candidate_slots) == {
            key for key, item in items.items() if item["submit_seen"]}
        counts["resource_candidates"] = len(candidates)
        counts["resource_keys"] = len(resource_keys)
        counts["resource_slot1_candidates"] = sum(
            1 in slots for slots in candidate_slots.values())

        resolutions = [(thread, row) for thread, row in events["resource resolution"]
                       if row["frame"] == source_frame]
        if resolutions:
            candidates_by_call = {(thread, row["call"]): row
                                  for thread, row in candidates}
            resolved_calls = set()
            objects_by_key = collections.defaultdict(set)
            for thread, resolution in resolutions:
                key = (thread, resolution["call"])
                assert key in candidates_by_call and key not in resolved_calls
                assert resolution["object"]
                resolved_calls.add(key)
                objects_by_key[candidates_by_call[key]["key"]].add(
                    resolution["object"])
            assert all(len(objects) == 1 for objects in objects_by_key.values())
            previous_keys = {}
            for thread, candidate in candidates:
                slot = (thread, candidate["slot"])
                call = (thread, candidate["call"])
                if slot in previous_keys:
                    assert (call in resolved_calls) == (
                        candidate["key"] != previous_keys[slot])
                previous_keys[slot] = candidate["key"]
            counts["resource_resolutions"] = len(resolutions)
            counts["resolved_resource_keys"] = len(objects_by_key)
            counts["resolved_resource_objects"] = len({
                obj for objects in objects_by_key.values() for obj in objects})

            binds = [(thread, row) for thread, row in events["resource bind"]
                     if row["frame"] == source_frame]
            if binds:
                assert len(binds) == len(resolutions)
                resolutions_by_call = {(thread, row["call"]): row
                                       for thread, row in resolutions}
                for thread, bind in binds:
                    key = (thread, bind["call"])
                    assert key in resolutions_by_call
                    assert bind["object"] == resolutions_by_call[key]["object"]
                    assert bind["slot"] == candidates_by_call[key]["slot"]
                    assert bind["context"] == items[key]["submit_context"]
                    assert bind["target"] == 0x82415C88
                counts["resource_binds"] = len(binds)

    second_targets = collections.defaultdict(collections.Counter)
    dispatches = [(thread, row) for thread, row in events["second track dispatch"]
                  if row["frame"] == source_frame]
    if dispatches:
        buckets = {(thread, row["ordinal"]): row for thread, row in entries}
        expected = {key for key, row in buckets.items() if not row["record"]}
        dispatched = set()
        for thread, dispatch in dispatches:
            key = (thread, dispatch["bucket_entry"])
            assert key in expected and key not in dispatched
            dispatched.add(key)
            bucket = buckets[key]
            assert dispatch["object"] == bucket["secondary_resolved"]
            target = SECOND_TARGETS[dispatch["target"]]
            second_targets[target]["entries"] += 1
            produced = 0
            for kind, label in (("semantic packet", "semantic"),
                                ("direct packet", "direct")):
                for ordinal in range(bucket["first_" + label],
                                     bucket["last_" + label] + 1):
                    packet = packets[kind][(thread, ordinal)]
                    second_targets[target]["packets"] += 1
                    second_targets[target]["draw_callbacks"] += draws[
                        packet["header_physical"]]
                    produced += 1
            second_targets[target]["producing_entries"] += bool(produced)
        assert dispatched == expected

    second_draws = [(thread, row) for thread, row in events["second draw call"]
                    if row["frame"] == source_frame]
    if second_draws:
        assert summary["second_draw_calls"] == len(second_draws) < summary["scope_limit"]
        assert not summary["unfinished_second_draw_scopes"]
        assert not summary["unmatched_second_draw_exits"]
        assert [row["ordinal"] for _, row in second_draws] == list(
            range(1, len(second_draws) + 1))
        buckets = {(thread, row["ordinal"]): row for thread, row in entries}
        target_by_bucket = {(thread, row["bucket_entry"]): row["target"]
                            for thread, row in dispatches}
        bound_enabled = any("bound_record" in row for _, row in second_draws)
        bound_records = collections.defaultdict(collections.Counter)
        bound_record_counts = {}
        binding_targets = collections.defaultdict(collections.Counter)
        fetches_by_record = collections.defaultdict(lambda: collections.defaultdict(set))
        records_by_fetch = collections.defaultdict(lambda: collections.defaultdict(set))
        child_packets = set()
        expected_second_packets = set()
        for (thread, _), bucket in buckets.items():
            if bucket["record"]:
                continue
            for kind, label in (("semantic packet", "semantic"),
                                ("direct packet", "direct")):
                expected_second_packets.update(
                    (kind, thread, ordinal)
                    for ordinal in range(bucket["first_" + label],
                                         bucket["last_" + label] + 1))
        for thread, draw in second_draws:
            key = (thread, draw["bucket_entry"])
            bucket = buckets[key]
            assert not bucket["record"]
            assert draw["target"] == target_by_bucket[key]
            target = SECOND_TARGETS[draw["target"]]
            assert target != "procedural_models"
            if bound_enabled and target in (
                    "procedural_characters", "procedural_vegetation"):
                assert draw["bound_context"] == draw["context"]
                assert draw["bound_slot"] == 0 and draw["bound_record"]
                if target == "procedural_characters":
                    assert draw["bound_record"] == bucket["secondary_resolved"] + 132
                bound_records[target][draw["bound_record"]] += 1
                if "bound_target" in draw:
                    assert draw["bound_target"] == 0x82415CA8
                    binding_targets[target][draw["bound_target"]] += 1
                if "bound_vertex_descriptor" in draw:
                    assert draw["bound_vertex_descriptor"]
                    assert draw["bound_vertex_size"] == draw["arg6"]
                record_key = (target, draw["bound_record"])
                assert (record_key not in bound_record_counts or
                        bound_record_counts[record_key] == draw["arg5"])
                bound_record_counts[record_key] = draw["arg5"]
            second_targets[target]["child_calls"] += 1
            produced = 0
            for kind, label in (("semantic packet", "semantic"),
                                ("direct packet", "direct")):
                assert bucket["first_" + label] <= draw["first_" + label]
                assert draw["last_" + label] <= bucket["last_" + label]
                for ordinal in range(draw["first_" + label],
                                     draw["last_" + label] + 1):
                    packet_key = (kind, thread, ordinal)
                    assert packet_key not in child_packets
                    child_packets.add(packet_key)
                    packet = packets[kind][(thread, ordinal)]
                    header = packet["header_physical"]
                    assert draws[header]
                    if fetch_signature_by_draw and target in (
                            "procedural_characters", "procedural_vegetation"):
                        backend_draws = prepared_by_header[header]
                        signatures = {fetch_signature_by_draw[draw_thread, backend["ordinal"]]
                                      for draw_thread, backend in backend_draws}
                        assert len(signatures) == 1
                        signature = next(iter(signatures))
                        assert len(signature) == 1 and signature[0][0] == 95
                        assert signature[0][1] and signature[0][2]
                        assert all(backend["index_buffer_type"] == 0 and
                                   backend["guest_primitive_type"] == 13
                                   for _, backend in backend_draws)
                        if "bound_vertex_descriptor" in draw:
                            assert signature[0][1] == (draw["bound_vertex_address"] &
                                                       0x1FFFFFFC)
                            assert signature[0][2] == (draw["bound_vertex_size"] &
                                                       0x03FFFFFC)
                            assert signature[0][4] == (draw["bound_vertex_address"] & 3)
                            second_targets[target]["title_fetch_matches"] += len(backend_draws)
                        fetches_by_record[target][draw["bound_record"]].add(signature)
                        records_by_fetch[target][signature].add(draw["bound_record"])
                    if target in ("procedural_characters", "procedural_vegetation"):
                        assert draw["arg4"] == 13
                        assert draw_index_counts[header] == {4 * draw["arg5"]}
                    produced += 1
            second_targets[target]["packetless_child_calls"] += not bool(produced)
        assert child_packets == expected_second_packets
        for target, records in bound_records.items():
            second_targets[target]["bound_records"] = len(records)
            second_targets[target]["bound_record_multiplicity"] = dict(sorted(
                collections.Counter(records.values()).items()))
            if binding_targets[target]:
                second_targets[target]["binding_targets"] = {
                    hex(address): count for address, count
                    in sorted(binding_targets[target].items())}
            if fetches_by_record[target]:
                assert all(len(signatures) == 1 for signatures in
                           fetches_by_record[target].values())
                assert all(len(bound) == 1 for bound in
                           records_by_fetch[target].values())
                second_targets[target]["vertex_fetch_signatures"] = len(
                    records_by_fetch[target])
        counts["second_draw_skips"] = summary["second_draw_skips"]

    if vertex_fetches:
        counts["prepared_vertex_fetches"] = len(vertex_fetches)
        counts.update({"fetch_origins_" + key: value for key, value in
                       fetch_origin_counts.items()})

    return {
        "source_frame": source_frame,
        "backend_frame": backend_frame,
        "view": hex(view),
        "presenter": hex(presenter),
        "entries": len(entries),
        "packet_headers": len(physical_headers),
        "descriptor_receivers": len(descriptor_bases),
        "first_models_with_items": len(first_models_with_items),
        "descriptor_kinds": {f"{path}:{kind}": count for (path, kind), count
                             in sorted(descriptor_kinds.items())},
        "second_targets": {name: dict(values) for name, values
                           in sorted(second_targets.items())},
        **dict(sorted(counts.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--backend-frame", type=int, required=True)
    parser.add_argument("--first-model-vtable", type=lambda value: int(value, 0))
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame, args.backend_frame,
                            args.first_model_vtable), indent=2))


if __name__ == "__main__":
    main()
