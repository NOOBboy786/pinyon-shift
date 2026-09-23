#!/usr/bin/env python3
"""Verify exact procedural-state packet and resource joins in one frame."""

import argparse
import collections
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()

    model, track, packets = {}, {}, {}
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
            track[thread] = (scope, row)
        elif "FH1 SNR01 track model end " in line:
            track.pop(thread)
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
            else:
                scope, selected = model[thread]
                path, state = "model", scope["arg6"]
            assert row["flush_owner"] == state + 0xE940
            key = row["header_physical"], row["target_physical"]
            assert key not in packets
            packets[key] = (path, selected["resource"], row)
            resources[path].add(selected["resource"])
    assert not model and not track and packets

    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    assert ledger["backend_frame"] == args.source_frame + 1
    draws = [row for row in ledger["draws"]
             if row["target"].startswith("14020500/")
             and row["classification"] == "view_owner"
             and row["flush_caller_lr"] == 0x824170BC]
    joined = collections.Counter()
    seen = set()
    for row in draws:
        key = row["execution_dispatch_packet_physical"], row["execution_command_buffer"]
        path, resource, packet = packets[key]
        assert row["scene_source_frame"] == packet["frame"] == args.source_frame
        assert row["owner"] == packet["flush_owner"]
        joined[(path, row["target"].split("/")[1])] += 1
        seen.add(key)
    assert seen == set(packets)
    print(json.dumps({
        "source_frame": args.source_frame,
        "scene_packets": len(packets),
        "candidate_draws": len(draws),
        "packets_by_path": dict(collections.Counter(path for path, _, _ in packets.values())),
        "resources_by_path": {path: len(values) for path, values in resources.items()},
        "draws_by_path_and_color": {f"{path}:{color}": count
                                    for (path, color), count in sorted(joined.items())},
    }, indent=2))


if __name__ == "__main__":
    main()
