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
                   r"direct packet|semantic packet|indexed packet|"
                   r"indexed2 owner|resident packet) (\{.*\})")


def verify(path: Path, frame: int):
    events = {kind: [] for kind in ("camera method", "view object400",
                                    "view end", "inline indirect write",
                                    "deferred indirect command",
                                    "primary indirect packet", "indirect buffer",
                                    "prepared draw", "direct packet",
                                    "semantic packet", "indexed packet",
                                    "indexed2 owner")}
    survey_ranges = []
    resident_writes = []
    for position, line in enumerate(path.open(encoding="utf-8-sig",
                                              errors="replace")):
        if "FH1 SNR01 resident packet survey active" in line:
            assert not survey_ranges
            survey_ranges = [(int(a, 16), int(b, 16)) for a, b in
                             re.findall(r"\[0x([0-9a-f]+),0x([0-9a-f]+)\)", line)]
            assert len(survey_ranges) == 2
        match = EVENT.search(line)
        if match:
            row = json.loads(match[3])
            row["_thread"] = int(match[1])
            if match[2] == "resident packet":
                resident_writes.append(row)
                continue
            if row["frame"] in (frame, frame + 1) or (
                    match[2] == "prepared draw" and row["frame"] == frame - 1):
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
    semantic = [row for _, row in events["semantic packet"]
                if row["frame"] == frame and row["header_physical"] in packets]
    indexed = [row for _, row in events["indexed packet"]
               if row["frame"] == frame and row["header_physical"] in packets]
    prior_packets = {row["packet_physical"] for _, row in
                     events["prepared draw"] if row["frame"] in (frame - 1, frame)}
    new_without_source_write = (packets - prior_packets) - {
        row["header_physical"] for row in direct + semantic + indexed}
    fields = ("vertex_shader", "pixel_shader", "index_count",
              "index_buffer_type", "index_buffer_guest_base",
              "index_buffer_length", "guest_primitive_type",
              "vertex_fetch_count", "texture_fetch_count")
    metadata = {}
    for _, row in events["prepared draw"]:
        if row["packet_physical"] in packets:
            key = (row["packet_physical"], row["frame"] == frame + 1)
            metadata.setdefault(key, set()).add(tuple(row[field] for field in fields))
    matching_prior_metadata = sum(
        metadata.get((packet, False)) == metadata.get((packet, True))
        for packet in packets & prior_packets)
    byte_hashes = {}
    for _, row in events["prepared draw"]:
        if row["packet_physical"] in packets and "packet_hash" in row:
            assert row["packet_bytes"] > 0
            key = (row["packet_physical"], row["frame"] == frame + 1)
            byte_hashes.setdefault(key, set()).add(
                (row["packet_bytes"], row["packet_hash"]))
    recurring_hashed = {packet for packet in packets & prior_packets
                        if (packet, False) in byte_hashes and
                        (packet, True) in byte_hashes}
    matching_prior_bytes = sum(
        byte_hashes[(packet, False)] == byte_hashes[(packet, True)]
        for packet in recurring_hashed)
    assert direct and all(
        (row["path"] == "indexed2_secondary" and not row["direct_call"] and
         ("indexed2_caller_lr" not in row or row["indexed2_caller_lr"])) or
        (row["path"] == "secondary" and row["direct_call"] and
         row["direct_caller_lr"])
        for row in direct)
    callers = Counter(row["indexed2_caller_lr"] for row in direct
                      if row["path"] == "indexed2_secondary" and
                      "indexed2_caller_lr" in row)
    scoped_callers = Counter(row["direct_caller_lr"] for row in direct
                             if row["path"] == "secondary")
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
        assert matching_prior_metadata == len(packets & prior_packets)
    return {"frame": frame, "main_camera": hex(main),
            "reflection_camera": hex(reflection),
            "view_calls": len(starts), "slot44_in_view": 8,
            "reflection_matrix144_changes": 6,
            "post_view_command": hex(command),
            "post_view_primary_packets": len(roots),
            "post_view_prepared_draws": len(draws),
            "post_view_unique_draw_packets": len(packets),
            "post_view_packet_addresses_seen_in_prior_frames": len(
                packets & prior_packets),
            "post_view_new_packet_addresses_without_source_write": len(
                new_without_source_write),
            "post_view_source_semantic_packets": len(semantic),
            "post_view_source_indexed_packets": len(indexed),
            "post_view_packet_addresses_with_matching_prior_metadata":
                matching_prior_metadata,
            "post_view_recurring_packet_byte_hashes_available": len(
                recurring_hashed),
            "post_view_recurring_packet_byte_hashes_matching":
                matching_prior_bytes,
            "resident_survey_active": bool(survey_ranges),
            "resident_survey_covered_recurring_addresses": sum(
                any(start <= packet < end for start, end in survey_ranges)
                for packet in packets & prior_packets),
            "resident_survey_total_writes": len(resident_writes),
            "resident_survey_recurring_writes": sum(
                row["header_physical"] in packets & prior_packets
                for row in resident_writes),
            "post_view_draws_by_root": {hex(root): count for root, count
                                        in sorted(draws_by_root.items())},
            "post_view_color_words": {hex(color): count for
                                      (_, color, _, _), count in targets.items()},
            "post_view_direct_packets_outside_scope": sum(
                not row["direct_call"] for row in direct),
            "post_view_direct_packets_inside_scope": sum(
                bool(row["direct_call"]) for row in direct),
            "title_owner_probe_matched": bool(owner),
            "post_view_indexed2_callers": {hex(caller): count for caller, count
                                           in sorted(callers.items())},
            "post_view_scoped_direct_callers": {
                hex(caller): count for caller, count in sorted(scoped_callers.items())}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame), indent=2))
