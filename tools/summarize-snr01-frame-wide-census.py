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
    title_draw_packets = {r["header_physical"]: (key, r)
                          for key in ("direct", "semantic")
                          for r in records[key]}
    assert len(primary) == len(records["primary"])
    assert len(scene) == len(records["scene"])
    assert len(title_draw_packets) == sum(len(records[key])
                                          for key in ("direct", "semantic"))
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

    target_classes = collections.defaultdict(collections.Counter)
    target_views = collections.defaultdict(collections.Counter)
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
        title_packet = title_draw_packets.get(draw["packet_physical"]) if not execution["parent"] else None
        if packet is None:
            classification = "unmatched_indirect" if execution["parent"] else "direct_root"
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
        target = (draw["surface_info"], draw["color_info"][0],
                  draw["depth_info"], draw["render_target_bits"])
        target_key = "/".join(f"{value:08X}" for value in target)
        target_classes[target_key][classification] += 1
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
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frames = [args.source_frame, args.source_frame + 1]
    records = read_records(args.log, set(frames), args.source_frame + 1)
    result = summarize(records, frames, args.source_frame + 1)
    result["log_sha256"] = hashlib.sha256(args.log.read_bytes()).hexdigest().upper()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()
