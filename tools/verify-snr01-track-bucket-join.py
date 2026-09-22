#!/usr/bin/env python3
"""Verify one bounded track bucket -> PM4 packet -> backend draw capture."""

import argparse
import collections
import json
import re
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (.*?) (\{.*\})")


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
    draws = collections.Counter(row["packet_physical"]
                                for _, row in events["prepared draw"]
                                if row["frame"] == backend_frame)
    draw_index_counts = collections.defaultdict(set)
    for _, row in events["prepared draw"]:
        if row["frame"] == backend_frame:
            draw_index_counts[row["packet_physical"]].add(row["index_count"])
    assert draws, "backend draw capture is missing"

    claimed = set()
    physical_headers = set()
    bucket_by_semantic = {}
    counts = collections.Counter()
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
                counts[path_name + "_packets"] += 1
                counts[path_name + "_draw_callbacks"] += callbacks
                produced += 1
        counts[path_name + "_producing_entries"] += bool(produced)
    assert len(physical_headers) == len(claimed), "packet header address reused"

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
