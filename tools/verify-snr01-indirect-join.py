#!/usr/bin/env python3
"""Check a bounded title primary-ring to backend indirect-draw join."""

import argparse
import collections
import json
from pathlib import Path


SOURCE = "FH1 SNR01 primary indirect packet "
DISPATCH = "FH1 SNR01 indirect buffer "
DRAW = "FH1 SNR01 prepared draw "


def verify(path: Path, source_frames: set[int], backend_frame: int) -> dict:
    source, dispatches, draws = [], [], []
    for line_number, line in enumerate(path.open(encoding="utf-8", errors="replace")):
        for marker, rows in ((SOURCE, source), (DISPATCH, dispatches), (DRAW, draws)):
            if marker in line:
                row = json.loads(line.split(marker, 1)[1])
                row["_line"] = line_number
                if (row["frame"] in source_frames if marker == SOURCE
                        else row["frame"] == backend_frame):
                    rows.append(row)
                break

    assert source and dispatches and draws, "capture is incomplete"
    assert len(dispatches) < 8192 and len(draws) < 8192, "trace cap may be hit"
    assert sorted(row["ordinal"] for row in dispatches) == list(range(1, len(dispatches) + 1))
    assert sorted(row["ordinal"] for row in draws) == list(range(1, len(draws) + 1))
    assert all(row["header_word"] == 0xC0013F00 for row in source)

    source_by_address = collections.defaultdict(list)
    for row in source:
        source_by_address[row["header_physical"]].append(row)
    by_id = {row["execution"]: row for row in dispatches}
    assert len(by_id) == len(dispatches), "execution ID reused"
    assert all(row["indirect_execution"] in by_id for row in draws), "draw execution missing"
    assert all(row["parent"] in by_id for row in dispatches if row["parent"]), "parent missing"
    for row in dispatches:
        if row["parent"]:
            parent = by_id[row["parent"]]
            assert (parent["command_buffer"] <= row["dispatch_packet_physical"] <
                    parent["command_buffer"] + parent["command_bytes"]), "child outside parent buffer"

    roots = {row["execution"]: row for row in dispatches if not row["parent"]}
    for root in roots.values():
        matches = source_by_address[root["dispatch_packet_physical"]]
        assert len(matches) == 1, "root has no unique source packet"
        assert matches[0]["gpu_target"] == root["command_buffer"], "root target differs"
        assert matches[0]["_line"] < root["_line"], "root executed before source write"

    def root_id(execution_id: int) -> int:
        seen = set()
        while by_id[execution_id]["parent"]:
            assert execution_id not in seen, "execution cycle"
            seen.add(execution_id)
            execution_id = by_id[execution_id]["parent"]
        return execution_id

    draw_sources = collections.Counter(
        source_by_address[roots[root_id(row["indirect_execution"])]["dispatch_packet_physical"]][0]["frame"]
        for row in draws
    )
    return {
        "backend_frame": backend_frame,
        "source_packets": {str(frame): sum(row["frame"] == frame for row in source)
                           for frame in sorted(source_frames)},
        "source_callers": {hex(caller): count for caller, count in sorted(
            collections.Counter(row["caller_lr"] for row in source).items())},
        "dispatches": len(dispatches),
        "roots": len(roots),
        "draws": len(draws),
        "draws_by_source_frame": dict(sorted(draw_sources.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frames", type=int, nargs="+", required=True)
    parser.add_argument("--backend-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, set(args.source_frames), args.backend_frame), indent=2))


if __name__ == "__main__":
    main()
