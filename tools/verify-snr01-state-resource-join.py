#!/usr/bin/env python3
"""Verify exact procedural-state packet and resource joins in one frame."""

import argparse
import collections
import json
import re
from pathlib import Path


def cached_version(row):
    if "instance_word12" not in row:
        return None
    assert row["parent_vtable"] == 0x82001D74
    version = row["instance_word12"] & 0xFFFF
    assert version == row["parent_word12"] >> 16
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--require-track-descriptor", action="store_true")
    parser.add_argument("--require-track-descriptor-words", action="store_true")
    args = parser.parse_args()

    model, track, packets = {}, {}, {}
    track_descriptors = {}
    selected_descriptors = set()
    matched_track_targets = 0
    resources = collections.defaultdict(set)
    for line in args.log.open(encoding="utf-8"):
        if "FH1 SNR01 " not in line or "{" not in line:
            continue
        match = re.search(r"\[t(\d+)\]", line)
        if not match:
            continue
        thread = int(match[1])
        row = json.loads(line[line.index("{"):])
        if row.get("frame") != args.source_frame:
            continue
        if "FH1 SNR01 second track dispatch " in line:
            assert thread not in model
            model[thread] = (row, None)
        elif "FH1 SNR01 procedural model resource " in line:
            scope, _ = model[thread]
            assert scope["target"] == 0x82417BC0
            assert row["vtable"] == 0x820019CC and row["ready"] == 1
            cached_version(row)
            model[thread] = (scope, row)
        elif "FH1 SNR01 track bucket entry " in line and thread in model:
            scope, _ = model.pop(thread)
            assert scope["bucket_entry"] == row["ordinal"]
        elif "FH1 SNR01 track model begin " in line:
            assert thread not in track
            track[thread] = (row, None)
        elif "FH1 SNR01 track model ready " in line:
            scope, selected = track[thread]
            assert selected is None and row["state_base"] == scope["state_base"]
            assert row["resource"] == scope["resource"]
            assert row["vtable"] == 0x820019CC and row["ready"] == 1
            cached_version(row)
            track[thread] = (scope, row)
        elif "FH1 SNR01 track descriptor " in line:
            scope, selected = track[thread]
            assert selected is not None and thread not in track_descriptors
            assert row["resource"] == selected["resource"]
            assert row["parent"] == selected["parent"]
            assert row["model_root"] and row["container"] == row["model_root"] + 128
            gate_word8 = row.get("gate_word8", row.get("count"))
            assert gate_word8 > 0 and row["table"] and row["descriptor"]
            assert row["index"] == row["selector_a"] * 3 + row["selector_b"]
            assert row["state"] == scope["state_base"] + 0xE940
            assert row["descriptor"] == row["state_descriptor"]
            track_descriptors[thread] = row
        elif "FH1 SNR01 track model end " in line:
            track.pop(thread)
            track_descriptors.pop(thread, None)
        elif ("FH1 SNR01 scene indirect packet " in line and
              row["view_call"] == 8 and row["flush_caller_lr"] == 0x824170BC):
            track_selected = thread in track and track[thread][1]
            model_selected = (thread in model and
                              model[thread][0]["target"] == 0x82417BC0 and
                              model[thread][1])
            assert bool(track_selected) != bool(model_selected)
            if track_selected:
                scope, selected = track[thread]
                path, state = "track", scope["state_base"]
                if args.require_track_descriptor or args.require_track_descriptor_words:
                    selected_descriptors.add(track_descriptors[thread]["descriptor"])
                if args.require_track_descriptor_words:
                    words = track_descriptors[thread]["words"]
                    assert len(words) == 8
                    assert words[4] & 0x1FFFFFFF == row["target_physical"]
                    matched_track_targets += 1
            else:
                scope, selected = model[thread]
                path, state = "model", scope["arg6"]
            assert row["flush_owner"] == state + 0xE940
            key = row["header_physical"], row["target_physical"]
            assert key not in packets
            packets[key] = (path, selected["resource"], row,
                            cached_version(selected),
                            track_descriptors[thread]["descriptor"]
                            if path == "track" and thread in track_descriptors else None)
            resources[path].add(selected["resource"])
    assert not model and not track and not track_descriptors and packets

    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    assert ledger["backend_frame"] == args.source_frame + 1
    draws = [row for row in ledger["draws"]
             if row["target"].startswith("14020500/")
             and row["classification"] == "view_owner"
             and row["flush_caller_lr"] == 0x824170BC]
    joined = collections.Counter()
    versions = collections.Counter()
    descriptor_draws = 0
    seen = set()
    for row in draws:
        key = row["execution_dispatch_packet_physical"], row["execution_command_buffer"]
        path, resource, packet, version, descriptor = packets[key]
        assert row["scene_source_frame"] == packet["frame"] == args.source_frame
        assert row["owner"] == packet["flush_owner"]
        joined[(path, row["target"].split("/")[1])] += 1
        if version is not None:
            versions[(path, version)] += 1
        if descriptor is not None:
            descriptor_draws += 1
        seen.add(key)
    assert seen == set(packets)
    if args.require_track_descriptor or args.require_track_descriptor_words:
        assert descriptor_draws == sum(count for (path, _), count in joined.items()
                                       if path == "track")
    print(json.dumps({
        "source_frame": args.source_frame,
        "scene_packets": len(packets),
        "candidate_draws": len(draws),
        "packets_by_path": dict(collections.Counter(path for path, *_ in packets.values())),
        "resources_by_path": {path: len(values) for path, values in resources.items()},
        "selected_track_descriptors": len(selected_descriptors),
        "track_packets_with_matched_command_target": matched_track_targets,
        "draws_with_track_descriptor": descriptor_draws,
        "draws_by_path_and_color": {f"{path}:{color}": count
                                    for (path, color), count in sorted(joined.items())},
        "draws_by_path_and_cached_version": {
            f"{path}:{version}": count for (path, version), count in sorted(versions.items())},
    }, indent=2))


if __name__ == "__main__":
    main()
