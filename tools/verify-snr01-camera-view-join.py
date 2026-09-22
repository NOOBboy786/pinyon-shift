#!/usr/bin/env python3
"""Check the bounded FH1 presentation-camera writer/view join."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (camera method|view object400|view end|"
                   r"render thread request begin|render thread request end|"
                   r"inline indirect write|deferred indirect command|"
                   r"primary indirect packet|indirect buffer|prepared draw|"
                   r"direct packet|semantic packet|indexed packet|"
                   r"indexed2 owner|resident packet|scene indirect packet|"
                   r"watch armed|watched page) (\{.*\})")


def verify(path: Path, frame: int):
    events = {kind: [] for kind in ("camera method", "view object400",
                                    "view end", "inline indirect write",
                                    "render thread request begin",
                                    "render thread request end",
                                    "deferred indirect command",
                                    "primary indirect packet", "indirect buffer",
                                    "prepared draw", "direct packet",
                                    "semantic packet", "indexed packet",
                                    "indexed2 owner", "watch armed",
                                    "watched page", "scene indirect packet")}
    survey_ranges = []
    resident_writes = []
    watch_active = False
    for position, line in enumerate(path.open(encoding="utf-8-sig",
                                              errors="replace")):
        if "FH1 SNR01 packet page watch active" in line:
            watch_active = True
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
                    match[2] in ("prepared draw", "watch armed") and
                    row["frame"] == frame - 1):
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
    request_begins = events["render thread request begin"]
    request_ends = events["render thread request end"]
    post_request = None
    if request_begins:
        end_by_ordinal = {row["ordinal"]: (position, row)
                          for position, row in request_ends}
        enclosing = [(begin, row, end_by_ordinal[row["ordinal"]])
                     for begin, row in request_begins
                     if row["ordinal"] in end_by_ordinal and
                     begin < post[0][0] < end_by_ordinal[row["ordinal"]][0]]
        assert len(enclosing) == 1
        begin, post_request, (end, ending) = enclosing[0]
        assert post_request["_thread"] == ending["_thread"] == post[0][1]["_thread"]
        assert (post_request["object"], post_request["mode"],
                post_request["request"]) == (
                    ending["object"], ending["mode"], ending["request"])
        assert post_request["mode"] == 1 and post_request["request"] == 0
        assert not any(begin < position < end for position, _ in starts)
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
    scene_packets = {(row["header_physical"], row["target_physical"]): row
                     for _, row in events["scene indirect packet"]
                     if row["frame"] == frame}
    assert len(scene_packets) == sum(row["frame"] == frame for _, row in
                                     events["scene indirect packet"])
    scene_children = [row for row in executions.values() if row["parent"]]
    scene_children_matched = sum(
        (row["dispatch_packet_physical"], row["command_buffer"])
        in scene_packets for row in scene_children)
    nested_draws = [draw for _, draw in draws
                    if executions[draw["indirect_execution"]]["parent"]]
    joined_draws = [
        scene_packets[(executions[draw["indirect_execution"]]
                       ["dispatch_packet_physical"], draw["command_buffer"])]
        for draw in nested_draws
        if (executions[draw["indirect_execution"]]
            ["dispatch_packet_physical"], draw["command_buffer"])
        in scene_packets]
    if scene_packets:
        assert len(joined_draws) == len(nested_draws)
        assert all(row["view_call"] == 8 and row["caller_lr"] for row in
                   joined_draws)
        assert all(row["flush_owner"] for row in joined_draws
                   if "flush_owner" in row and row.get("flush_caller_lr") in
                   (0x824399F0, 0x8243CE0C, 0x8241A2A4, 0x824170BC))
        car_owner_vtables = {0x8243CE0C: 0x82003A54,
                             0x824399F0: 0x82001618,
                             0x8241A2A4: 0x82001618}
        assert all(row["flush_owner_first_word"] ==
                   car_owner_vtables[row["flush_caller_lr"]]
                   for row in joined_draws
                   if "flush_owner_first_word" in row and
                   row.get("flush_caller_lr") in car_owner_vtables)
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
    recurring_pages = {packet & ~0xFFF for packet in packets & prior_packets}
    armed_pages = {row["page"] for _, row in events["watch armed"]}
    touched_pages = {row["page"] for _, row in events["watched page"]
                     if row["is_write"]}
    if watch_active:
        assert recurring_pages <= armed_pages
        assert not any("trace limit reached" in line for line in
                       path.open(encoding="utf-8-sig", errors="replace"))
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
            "post_view_render_thread_mode": (
                post_request["mode"] if post_request else None),
            "post_view_render_thread_request": (
                post_request["request"] if post_request else None),
            "post_view_primary_packets": len(roots),
            "post_view_prepared_draws": len(draws),
            "scene_child_executions": (
                len(scene_children) if scene_packets else None),
            "scene_child_executions_matched": (
                scene_children_matched if scene_packets else None),
            "post_view_nested_draws": len(nested_draws),
            "post_view_nested_draws_joined_to_scene_lists": (
                len(joined_draws) if scene_packets else None),
            "post_view_scene_list_objects": (
                len({row["list_object"] for row in joined_draws})
                if scene_packets else None),
            "post_view_scene_flush_callers": dict(Counter(
                hex(row["flush_caller_lr"]) for row in joined_draws
                if "flush_caller_lr" in row)),
            "post_view_scene_owner_first_words": dict(Counter(
                hex(row["flush_owner_first_word"]) for row in joined_draws
                if "flush_owner_first_word" in row)),
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
            "packet_page_watch_active": watch_active,
            "post_view_recurring_pages_armed": len(recurring_pages & armed_pages),
            "post_view_recurring_pages_touched": len(recurring_pages & touched_pages),
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
