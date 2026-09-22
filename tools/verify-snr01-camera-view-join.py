#!/usr/bin/env python3
"""Check the bounded FH1 presentation-camera writer/view join."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (camera method|view object400|view end|"
                   r"inline indirect write|deferred indirect command|"
                   r"primary indirect packet|indirect buffer|prepared draw|"
                   r"direct packet|indexed2 owner) (\{.*\})")


def verify(path: Path, frame: int):
    events = {kind: [] for kind in ("camera method", "view object400",
                                    "view end", "inline indirect write",
                                    "deferred indirect command",
                                    "primary indirect packet", "indirect buffer",
                                    "prepared draw", "direct packet",
                                    "indexed2 owner")}
    for position, line in enumerate(path.open(encoding="utf-8-sig",
                                              errors="replace")):
        match = EVENT.search(line)
        if match:
            row = json.loads(match[3])
            row["_thread"] = int(match[1])
            if row["frame"] in (frame, frame + 1):
                events[match[2]].append((position, row))

    starts, ends = events["view object400"], events["view end"]
    assert len(starts) == len(ends) == 8
    assert len({row["_thread"] for _, row in starts + ends}) == 1
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
            if row["frame"] == frame and
            row["request_caller_lr"] == 0x8245B870]
    assert len(post) == 1 and post[0][0] > ends[-1][0]
    assert post[0][1]["_thread"] == ends[-1][1]["_thread"]
    assert post[0][1]["view_call"] == post[0][1]["view"] == 0
    command = post[0][1]["command_physical"]
    reads = [(position, row) for position, row in
             events["deferred indirect command"]
             if row["frame"] == frame + 1 and
             row["command_physical"] == command]
    roots = {row["header_physical"]: row for _, row in
             events["primary indirect packet"]
             if row["frame"] == frame + 1 and
             row["worker_command_physical"] == command}
    assert reads and len(reads) == len(roots)
    assert all(position > post[0][0] and
               (row["opcode"], row["payload"]) ==
               (post[0][1]["opcode"], post[0][1]["payload"])
               for position, row in reads)
    assert {row["worker_stream"] for _, row in reads} == {
        row["worker_stream"] for row in roots.values()}

    executions = {row["execution"]: row for _, row in
                  events["indirect buffer"] if row["frame"] == frame + 1}
    draws = []
    for _, draw in events["prepared draw"]:
        if draw["frame"] != frame + 1 or not draw["indirect_execution"]:
            continue
        execution = draw["indirect_execution"]
        while executions[execution]["parent"]:
            execution = executions[execution]["parent"]
        header = executions[execution]["dispatch_packet_physical"]
        if header in roots:
            draws.append((header, draw))
    packets = {draw["packet_physical"] for _, draw in draws}
    draws_by_root = Counter(header for header, _ in draws)
    assert packets and all(draws_by_root[root] for root in roots)
    targets = Counter((draw["surface_info"], draw["color_info"][0],
                       draw["depth_info"], draw["render_target_bits"])
                      for _, draw in draws)
    assert all(surface == 0x14020500 and color in (0xC0000, 0x30000)
               and depth == 0x10400 and bits == 3
               for surface, color, depth, bits in targets)
    direct = [row for _, row in events["direct packet"]
              if row["frame"] == frame and row["header_physical"] in packets]
    assert direct and all(row["direct_call"] == 0 and
                          row["path"] == "indexed2_secondary" for row in direct)
    callers = Counter(row.get("indexed2_caller_lr", 0) for row in direct)
    if any("indexed2_caller_lr" in row for row in direct):
        assert 0 not in callers
    owner = events["indexed2 owner"]
    if owner:
        assert len(owner) == 1
        owner_position, owner_row = owner[0]
        assert starts[-1][0] < owner_position < ends[-1][0]
        assert owner_row["_thread"] == ends[-1][1]["_thread"]
        assert owner_row["view_call"] == 8
        assert owner_row["caller_lr"] == 0x82446164
        assert owner_row["arg5"] == starts[-1][1]["view"]
        title_direct = [(position, row) for position, row in
                        events["direct packet"]
                        if row["frame"] == frame and
                        row.get("indexed2_caller_lr") == 0x8244F070]
        assert len(title_direct) == 1
        assert owner_position < title_direct[0][0] < ends[-1][0]
        assert title_direct[0][1]["header_physical"] in packets
    return {"frame": frame, "main_camera": hex(main),
            "reflection_camera": hex(reflection),
            "view_calls": len(starts), "slot44_in_view": 8,
            "reflection_matrix144_changes": 6,
            "post_view_command": hex(command),
            "post_view_primary_packets": len(roots),
            "post_view_prepared_draws": len(draws),
            "post_view_unique_draw_packets": len(packets),
            "post_view_draws_by_root": {hex(root): count for root, count
                                        in sorted(draws_by_root.items())},
            "post_view_color_words": {hex(color): count for
                                      (_, color, _, _), count in targets.items()},
            "post_view_direct_packets_outside_scope": len(direct),
            "title_owner_probe_matched": bool(owner),
            "post_view_indexed2_callers": {hex(caller): count for caller, count
                                           in sorted(callers.items())}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame), indent=2))
