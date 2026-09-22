#!/usr/bin/env python3
"""Account for every prepared draw in one backend frame by title view/owner."""

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


PREFIXES = {
    "primary": "FH1 SNR01 primary indirect packet ",
    "scene": "FH1 SNR01 scene indirect packet ",
    "execution": "FH1 SNR01 indirect buffer ",
    "draw": "FH1 SNR01 prepared draw ",
    "view_begin": "FH1 SNR01 view begin ",
    "view_end": "FH1 SNR01 view end ",
    "direct": "FH1 SNR01 direct packet ",
    "semantic": "FH1 SNR01 semantic packet ",
    "item_node": "FH1 SNR01 item node ",
    "item": "FH1 SNR01 procedural item ",
    "second_path": "FH1 SNR01 second path ",
    "second_draw": "FH1 SNR01 second draw call ",
    "family_record": "FH1 SNR01 direct family record ",
    "family": "FH1 SNR01 direct family ",
    "clear": "FH1 clear producer ",
}


def read_records(path, frames, backend_frame):
    records = {key: [] for key in PREFIXES}
    view_scopes = collections.defaultdict(list)
    with path.open(encoding="utf-8", errors="replace") as source:
        for line in source:
            for key, prefix in PREFIXES.items():
                if prefix in line:
                    row = json.loads(line.split(prefix, 1)[1])
                    if row["frame"] in (frames if key not in ("execution", "draw")
                                        else {backend_frame}):
                        if key in ("view_begin", "view_end", "direct", "semantic"):
                            thread = int(re.search(r"\[t(\d+)\]", line)[1])
                            scope = view_scopes[thread]
                            if key == "view_begin":
                                scope.append(row)
                            elif key == "view_end":
                                assert scope and scope.pop()["call"] == row["call"]
                            else:
                                row["title_view_call"] = scope[-1]["call"] if scope else 0
                                row["title_view"] = scope[-1]["view"] if scope else 0
                        records[key].append(row)
                    break
    assert all(not scope for scope in view_scopes.values())
    return records


def summarize(records, frames, backend_frame):
    assert len(frames) == 2 and frames[1] == frames[0] + 1
    views = {}
    for frame in frames:
        starts = [r for r in records["view_begin"] if r["frame"] == frame]
        ends = [r for r in records["view_end"] if r["frame"] == frame]
        assert [r["call"] for r in starts] == list(range(1, 9))
        assert [r["call"] for r in ends] == list(range(1, 9))
        views[frame] = {r["call"]: r for r in starts}
        assert all(a["view"] == b["view"] for a, b in zip(starts, ends))

    primary = {(r["header_physical"], r["gpu_target"]): r
               for r in records["primary"]}
    scene = {(r["header_physical"], r["target_physical"]): r
             for r in records["scene"]}
    title_draw_packets = collections.defaultdict(list)
    for key in ("direct", "semantic"):
        for row in records[key]:
            title_draw_packets[row["header_physical"]].append((key, row))
    families = collections.defaultdict(list)
    for row in records["family"]:
        families[row["frame"]].append(row)
    family_records = {(r["frame"], r["next_direct"]): r
                      for r in records["family_record"]}
    assert len(family_records) == len(records["family_record"])
    items = {(r["frame"], r["call"]): r for r in records["item"]}
    assert len(items) == len(records["item"])
    item_nodes = {}
    for node in records["item_node"]:
        for ordinal in range(node["first_semantic"], node["last_semantic"] + 1):
            key = (node["frame"], ordinal)
            assert key not in item_nodes, f"overlapping item nodes: {key}"
            item_nodes[key] = node
    second_paths = {}
    for scope in records["second_path"]:
        for ordinal in range(scope["first_semantic"], scope["last_semantic"] + 1):
            key = (scope["frame"], ordinal)
            assert key not in second_paths, f"overlapping second paths: {key}"
            second_paths[key] = scope
    second_draws = {}
    for scope in records["second_draw"]:
        for ordinal in range(scope["first_semantic"], scope["last_semantic"] + 1):
            key = (scope["frame"], ordinal)
            assert key not in second_draws, f"overlapping second draws: {key}"
            second_draws[key] = scope
    assert len(primary) == len(records["primary"])
    assert len(scene) == len(records["scene"])
    assert all(r["view_call"] == 0 or
               r["view"] == views[r["frame"]][r["view_call"]]["view"]
               for r in scene.values())
    executions = {r["execution"]: r for r in records["execution"]}
    assert len(executions) == len(records["execution"])
    roots = [r for r in executions.values() if not r["parent"]]
    assert roots and len(records["draw"]) < 8192
    root_sources = {}
    for root in roots:
        key = root["dispatch_packet_physical"], root["command_buffer"]
        assert key in primary, f"root without title packet: {key}"
        root_sources[root["execution"]] = primary[key]

    clear_ranges = collections.defaultdict(list)
    for row in records["clear"]:
        if (row.get("refills") or row.get("nested") or
                "command_cursor_before" not in row or
                "command_cursor_after" not in row):
            continue
        begin = row["command_cursor_before"] & 0x1FFFFFFF
        end = row["command_cursor_after"] & 0x1FFFFFFF
        # ponytail: cap joins at 4 KiB; broaden only with buffer-lifetime proof.
        if begin < end and end - begin <= 4096:
            clear_ranges[row["frame"]].append((begin, end, row))

    target_classes = collections.defaultdict(collections.Counter)
    target_views = collections.defaultdict(collections.Counter)
    target_no_attachment_write = collections.Counter()
    source_frames = collections.Counter()
    scene_frames = collections.Counter()
    direct_views = collections.Counter()
    classifications = collections.Counter()
    detail = []
    for draw in records["draw"]:
        execution = executions[draw["indirect_execution"]]
        root = execution
        seen = set()
        while root["parent"]:
            assert root["execution"] not in seen
            seen.add(root["execution"])
            root = executions[root["parent"]]
        source = root_sources[root["execution"]]
        source_frames[source["frame"]] += 1
        packet = scene.get((execution["dispatch_packet_physical"],
                            execution["command_buffer"])) if execution["parent"] else None
        title_matches = title_draw_packets.get(draw["packet_physical"], [])
        if not execution["parent"]:
            assert len(title_matches) <= 1, f"ambiguous title packet: {draw['ordinal']}"
        title_packet = title_matches[0] if title_matches and not execution["parent"] else None
        clear_producer = None
        if (not execution["parent"] and title_packet is None and
                draw.get("packet_bytes", 0) > 0):
            end = draw["packet_physical"] + draw["packet_bytes"]
            matches = [row for begin, limit, row in clear_ranges[source["frame"]]
                       if begin <= draw["packet_physical"] and end <= limit]
            assert len(matches) <= 1, f"ambiguous clear producer for draw {draw['ordinal']}"
            clear_producer = matches[0] if matches else None
        if packet is None:
            classification = ("unmatched_indirect" if execution["parent"] else
                              "title_clear" if clear_producer else "direct_root")
        elif not packet["view_call"]:
            classification = "out_of_view_scene"
        elif not packet["flush_owner"]:
            classification = "view_unowned"
        else:
            classification = "view_owner"
        if packet and packet["view_call"]:
            assert packet["frame"] in frames
            assert packet["view_call"] in views[packet["frame"]]
            assert packet["view"] == views[packet["frame"]][packet["view_call"]]["view"]
        if packet:
            scene_frames[packet["frame"]] += 1
        if title_packet:
            title_key, title_row = title_packet
            if title_row["title_view_call"]:
                assert title_row["title_view"] == views[title_row["frame"]][
                    title_row["title_view_call"]]["view"]
            direct_views[f'{title_row["frame"]}:{title_row["title_view_call"]}'] += 1
        family = None
        family_record = None
        item = None
        item_node = None
        second_path = None
        second_draw = None
        if title_packet and title_packet[0] == "semantic":
            title_row = title_packet[1]
            key = (title_row["frame"], title_row["ordinal"])
            item_node = item_nodes.get(key)
            second_path = second_paths.get(key)
            second_draw = second_draws.get(key)
            if title_row["emitter_caller_lr"] == 0x82412E1C and records["second_path"]:
                assert second_path, f"missing second path: {draw['ordinal']}"
            if second_path:
                assert title_row["emitter_caller_lr"] == 0x82412E1C
                assert second_path["view_call"] == title_row["title_view_call"]
            if second_draw and second_path:
                assert second_draw["context"] == second_path["context"]
                assert second_draw["arg4"] == second_path["arg4"]
                assert second_draw["arg5"] == second_path["arg5"]
                assert second_draw["arg6"] == second_path["arg6"]
                if second_path["caller_lr"] == 0x82413A84:
                    assert second_draw["vegetation_owner"]
                    assert second_draw["bound_record"] == second_draw["vegetation_selected_record"]
                    assert second_draw["bound_vertex_descriptor"]
            if title_row["procedural_call"]:
                item = items.get((title_row["frame"], title_row["procedural_call"]))
                if records["item"]:
                    assert item, f"missing procedural item: {draw['ordinal']}"
                if item:
                    assert item["receiver"] == title_row["procedural_receiver"]
                    assert item["first_semantic_packet"] <= title_row["ordinal"] <= item["last_semantic_packet"]
                    assert item["descriptor_seen"] and item["runtime_seen"] and item["submit_seen"]
            if records["item_node"]:
                assert bool(item_node) == bool(item), f"item/node gap: {draw['ordinal']}"
            if item_node:
                assert item_node["view_call"] == title_row["title_view_call"]
                assert item_node["first_item"] <= item["call"] <= item_node["last_item"]
                assert item_node["receiver"] == item["receiver"]
        if title_packet and title_packet[0] == "direct":
            title_row = title_packet[1]
            matches = [row for row in families[title_row["frame"]]
                       if row["first_direct"] <= title_row["ordinal"]
                       <= row["last_direct"]]
            assert len(matches) <= 1, f"ambiguous direct family: {draw['ordinal']}"
            family = matches[0] if matches else None
            if family:
                assert family["view_call"] == title_row["title_view_call"]
            family_record = family_records.get((title_row["frame"], title_row["ordinal"]))
            if family_record:
                assert family and family_record["family_call"] == family["call"]
                assert family_record["view_call"] == title_row["title_view_call"]
                assert family_record["arg7"] == draw["index_count"], (
                    f"record/draw index count differs: {draw['ordinal']}")
            if families[title_row["frame"]] and title_row["direct_caller_lr"] == 0x8243C8FC:
                assert family, f"missing direct family: {draw['ordinal']}"
                if records["family_record"]:
                    assert family_record, f"missing direct record: {draw['ordinal']}"
        target = (draw["surface_info"], draw["color_info"][0],
                  draw["depth_info"], draw["render_target_bits"])
        target_key = "/".join(f"{value:08X}" for value in target)
        no_attachment_write = (
            draw.get("color_mask") == 0 and
            draw.get("depth_control") is not None and
            draw["depth_control"] & 7 == 0
        )
        target_classes[target_key][classification] += 1
        target_no_attachment_write[target_key] += no_attachment_write
        if packet:
            target_views[target_key][f'{packet["frame"]}:{packet["view_call"]}'] += 1
        classifications[classification] += 1
        detail.append({
            "ordinal": draw["ordinal"],
            "target": target_key,
            "classification": classification,
            "packet_physical": draw["packet_physical"],
            "execution": execution["execution"],
            "execution_dispatch_packet_physical": execution["dispatch_packet_physical"],
            "execution_command_buffer": execution["command_buffer"],
            "root_execution": root["execution"],
            "root_dispatch_packet_physical": root["dispatch_packet_physical"],
            "root_command_buffer": root["command_buffer"],
            "root_source_frame": source["frame"],
            "root_queued_caller_lr": source.get("queued_caller_lr", 0),
            "scene_source_frame": packet["frame"] if packet else None,
            "view_call": packet["view_call"] if packet else None,
            "owner": packet["flush_owner"] if packet else None,
            "owner_first_word": packet["flush_owner_first_word"] if packet else None,
            "flush_caller_lr": packet["flush_caller_lr"] if packet else None,
            "vertex_shader": draw.get("vertex_shader"),
            "pixel_shader": draw.get("pixel_shader"),
            "index_count": draw.get("index_count"),
            "depth_control": draw.get("depth_control"),
            "color_mask": draw.get("color_mask"),
            "draw_flags": draw.get("draw_flags"),
            "no_attachment_write": no_attachment_write,
            "title_packet_kind": title_packet[0] if title_packet else None,
            "title_packet_path": title_packet[1].get("path") if title_packet else None,
            "title_packet_source_frame": title_packet[1]["frame"] if title_packet else None,
            "title_packet_view_call": title_packet[1]["title_view_call"] if title_packet else None,
            "title_packet_caller_lr": (
                title_packet[1].get("direct_caller_lr") or
                title_packet[1].get("indexed2_caller_lr") or
                title_packet[1].get("emitter_caller_lr") or 0
            ) if title_packet else None,
            "title_packet_receiver": (
                title_packet[1].get("procedural_receiver") or
                title_packet[1].get("dispatch_receiver") or 0
            ) if title_packet else None,
            "title_direct_family_call": family["call"] if family else None,
            "title_direct_family_object": family["object"] if family else None,
            "title_direct_family_list": family["list"] if family else None,
            "title_direct_record": family_record["record"] if family_record else None,
            "title_direct_record_words": family_record["record_words"] if family_record else None,
            "title_direct_record_source": family_record["source"] if family_record else None,
            "title_direct_record_arg6": family_record["arg6"] if family_record else None,
            "title_direct_record_arg7": family_record["arg7"] if family_record else None,
            "title_item_call": item["call"] if item else None,
            "title_item_receiver": item["receiver"] if item else None,
            "title_item_descriptor": item["descriptor_address"] if item else None,
            "title_item_descriptor_index": item["descriptor_index"] if item else None,
            "title_item_descriptor_kind": item["descriptor_kind"] if item else None,
            "title_item_runtime": item["runtime_address"] if item else None,
            "title_item_node": item_node["node"] if item_node else None,
            "title_item_node_index": item_node["index"] if item_node else None,
            "title_item_list_head": item_node["list_head"] if item_node else None,
            "title_item_render_owner": item_node["render_owner"] if item_node else None,
            "title_item_bucket_entry": item_node["bucket_entry"] if item_node else None,
            "title_second_path_caller_lr": second_path["caller_lr"] if second_path else None,
            "title_second_path_context": second_path["context"] if second_path else None,
            "title_second_path_arg4": second_path["arg4"] if second_path else None,
            "title_second_path_arg5": second_path["arg5"] if second_path else None,
            "title_second_draw_bucket_entry": second_draw["bucket_entry"] if second_draw else None,
            "title_second_draw_target": second_draw["target"] if second_draw else None,
            "title_second_draw_bound_record": second_draw["bound_record"] if second_draw else None,
            "title_second_draw_vertex_descriptor": second_draw["bound_vertex_descriptor"] if second_draw else None,
            "title_second_draw_vegetation_owner": second_draw["vegetation_owner"] if second_draw else None,
            "clear_producer_record": clear_producer["record"] if clear_producer else None,
            "clear_producer_flags": clear_producer["flags"] if clear_producer else None,
        })
    assert sorted(r["ordinal"] for r in detail) == list(range(1, len(detail) + 1))
    assert sum(classifications.values()) == len(records["draw"])
    return {
        "schema": "pinyon-shift.snr01-frame-wide-census.v1",
        "source_frames": frames,
        "backend_frame": backend_frame,
        "totals": {
            "draws": len(detail), "roots": len(roots),
            "executions": len(executions),
            "scene_packets": len(scene),
            "classifications": dict(classifications),
            "draws_by_root_source_frame": dict(sorted(source_frames.items())),
            "draws_by_scene_source_frame": dict(sorted(scene_frames.items())),
            "direct_root_draws_by_title_view": dict(sorted(direct_views.items())),
        },
        "targets": {
            target: {"draws": sum(classes.values()),
                     "classifications": dict(classes),
                     "no_attachment_write_draws": target_no_attachment_write[target],
                     "scene_views": dict(target_views[target])}
            for target, classes in sorted(target_classes.items())
        },
        "draws": detail,
        "safety": {"metadata_only": True, "suppression_allowed": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--require-direct-family", action="store_true")
    parser.add_argument("--require-direct-family-record", action="store_true")
    parser.add_argument("--require-semantic-item-node", action="store_true")
    parser.add_argument("--require-second-path", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frames = [args.source_frame, args.source_frame + 1]
    records = read_records(args.log, set(frames), args.source_frame + 1)
    if args.require_direct_family:
        assert records["family"], "no bounded direct-family scopes"
    if args.require_direct_family_record:
        assert records["family"] and records["family_record"], "no direct-family records"
    if args.require_semantic_item_node:
        assert records["item"] and records["item_node"], "no item-node records"
    if args.require_second_path:
        assert records["second_path"], "no second-path records"
    result = summarize(records, frames, args.source_frame + 1)
    result["log_sha256"] = hashlib.sha256(args.log.read_bytes()).hexdigest().upper()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()
