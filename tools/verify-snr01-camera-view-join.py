#!/usr/bin/env python3
"""Check the bounded FH1 presentation-camera writer/view join."""

import argparse
import json
import re
from pathlib import Path


EVENT = re.compile(r"FH1 SNR01 (camera method|view object400|view end|"
                   r"inline indirect write) (\{.*\})")


def verify(path: Path, frame: int):
    events = {kind: [] for kind in ("camera method", "view object400",
                                    "view end", "inline indirect write")}
    for position, line in enumerate(path.open(encoding="utf-8-sig",
                                              errors="replace")):
        match = EVENT.search(line)
        if match:
            row = json.loads(match[2])
            if row["frame"] == frame:
                events[match[1]].append((position, row))

    starts, ends = events["view object400"], events["view end"]
    assert len(starts) == len(ends) == 8
    assert [row["call"] for _, row in starts] == list(range(1, 9))
    assert [row["call"] for _, row in ends] == list(range(1, 9))
    main = starts[0][1]["object"]
    reflection = starts[1][1]["object"]
    assert main != reflection and main == starts[-1][1]["object"]
    assert all(row["object"] == reflection for _, row in starts[1:7])
    assert all(a["object"] == b["camera"] and a["matrix80_hash"] ==
               b["matrix80_hash"] for (_, a), (_, b) in zip(starts, ends))
    assert all(a["matrix144_hash"] != b["matrix144_hash"]
               for (_, a), (_, b) in zip(starts[1:7], ends[1:7]))
    assert all(starts[i][1]["matrix144_hash"] ==
               ends[i][1]["matrix144_hash"] for i in (0, 7))
    assert all(ends[i][1]["matrix144_hash"] ==
               starts[i + 1][1]["matrix144_hash"] for i in range(1, 6))

    methods = [row for _, row in events["camera method"]]
    assert [(row["view_call"], row["camera"]) for row in methods
            if row["slot"] == 44 and row["view_call"]] == [
                (row["call"], row["object"]) for _, row in starts]
    assert any(row["slot"] == 11 and row["camera"] == main and
               row["view_call"] == 0 for row in methods)
    post = [(position, row) for position, row in events["inline indirect write"]
            if row["request_caller_lr"] == 0x8245B870]
    assert len(post) == 1 and post[0][0] > ends[-1][0]
    assert post[0][1]["view_call"] == post[0][1]["view"] == 0
    return {"frame": frame, "main_camera": hex(main),
            "reflection_camera": hex(reflection),
            "view_calls": len(starts), "slot44_in_view": 8,
            "reflection_matrix144_changes": 6,
            "post_view_command": hex(post[0][1]["command_physical"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame), indent=2))
