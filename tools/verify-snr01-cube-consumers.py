#!/usr/bin/env python3
"""Join one reflection-cube copy sequence to its live texture-fetch consumers."""

import argparse
import collections
import json
import re
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (.*?) (\{.*\})")
FACE_ORDER = [0, 4, 2, 1, 3, 5]
FACE_BYTES = 256 * 256 * 4


def verify(path: Path, source_frame: int, backend_frame: int,
           allow_missing_view_trace: bool = False,
           require_command_writers: bool = False):
    events = collections.defaultdict(list)
    for line_number, line in enumerate(path.open(encoding="utf-8-sig",
                                                  errors="replace")):
        match = EVENT.search(line)
        if match:
            row = json.loads(match[3])
            if row["frame"] in (source_frame, backend_frame) or (
                require_command_writers and
                match[2] in ("linked indirect write", "inline indirect write",
                             "view object400") and
                source_frame - 12 <= row["frame"] <= source_frame
            ):
                events[match[2]].append((line_number, int(match[1]), row))

    copies = [(position, row) for position, _, row in events["copy"]
              if row["frame"] == backend_frame and row["succeeded"] and
              (row["resolve_width"], row["resolve_height"],
               row["written_length"]) == (256, 256, FACE_BYTES)]
    groups = collections.defaultdict(list)
    for position, row in copies:
        groups[(row["surface_info"], tuple(row["color_info"]),
                row["depth_info"])].append((position, row))
    faces = [group for group in groups.values() if len(group) == 6]
    assert len(faces) == 1, "reflection face copy group is ambiguous"
    faces = faces[0]
    base = min(row["dest_base"] for _, row in faces)
    assert [row["dest_base"] - base for _, row in faces] == [
        face * FACE_BYTES for face in FACE_ORDER]
    assert [row["ordinal"] for _, row in faces] == list(
        range(faces[0][1]["ordinal"], faces[0][1]["ordinal"] + 6))

    prepared = {row["ordinal"]: (position, row)
                for position, _, row in events["prepared draw"]
                if row["frame"] == backend_frame}
    assert len(prepared) == sum(row["frame"] == backend_frame
                                for _, _, row in events["prepared draw"])
    assert sorted(prepared) == list(range(1, len(prepared) + 1))
    all_fetches = [row for _, _, row in events["prepared texture fetch"]
                   if row["frame"] == backend_frame]
    assert sum(row["texture_fetch_count"] for _, row in prepared.values()) == len(
        all_fetches), "texture-fetch trace is incomplete"
    consumers = [(position, row) for position, _, row in
                 events["prepared texture fetch"]
                 if row["frame"] == backend_frame and
                 row["base_address"] == base]
    assert consumers and all(position > faces[-1][0]
                             for position, _ in consumers)
    assert all((row["type"], row["dimension"], row["width"],
                row["height"], row["stack_depth"]) == (2, 3, 256, 256, 6)
               for _, row in consumers)
    descriptors = {(row["format"], row["mip_address"])
                   for _, row in consumers}
    assert descriptors == {(54, base + 6 * FACE_BYTES)}
    assert len({row["draw"] for _, row in consumers}) == len(consumers)
    assert all(row["draw"] in prepared and
               prepared[row["draw"]][1]["packet_physical"] ==
               row["packet_physical"] for _, row in consumers)

    dispatches = {row["execution"]: row for _, _, row in
                  events["indirect buffer"] if row["frame"] == backend_frame}
    primary = {row["header_physical"]: (position, row) for position, _, row in
               events["primary indirect packet"]
               if row["frame"] == source_frame}
    assert dispatches and primary

    def source_for(draw):
        execution = draw["indirect_execution"]
        while dispatches[execution]["parent"]:
            execution = dispatches[execution]["parent"]
        return primary[dispatches[execution]["dispatch_packet_physical"]]

    commands = events["deferred indirect command"]
    writers = events["linked indirect write"] + events["inline indirect write"]
    cameras = {(row["frame"], thread, row["call"]): row
               for _, thread, row in events["view object400"]}
    assert len(cameras) == len(events["view object400"])
    command_writers = {}

    def writer_for(packet_position, source):
        address = source["worker_command_physical"]
        reads = [(position, row) for position, _, row in commands
                 if position <= packet_position and
                 row["command_physical"] == address]
        assert reads, f"no deferred command read for {address:#x}"
        read_position, read = max(reads, key=lambda item: item[0])
        candidates = [(position, thread, row) for position, thread, row in writers
                      if position < read_position and
                      (row.get("command_physical",
                               row.get("opcode_address", 0) & 0x1FFFFFFF) == address)]
        assert candidates, f"no prior command writer for {address:#x}"
        _, writer_thread, writer = max(candidates, key=lambda item: item[0])
        assert (read["opcode"], read["payload"]) == (
            writer["opcode"], writer["payload"]), (
                f"command {address:#x} changed between write and read")
        assert read["worker_stream"] == source["worker_stream"]
        camera = cameras.get((writer["frame"], writer_thread,
                              writer["view_call"])) if writer["view_call"] else None
        if camera:
            assert camera["view"] == writer["view"]
        return {"address": hex(address), "writer_frame": writer["frame"],
                "writer_path": writer.get("path", "linked"),
                "writer_refill_caller_lr": hex(writer.get("refill_caller_lr", 0)),
                "writer_request_caller_lr": hex(writer.get("request_caller_lr", 0)),
                "writer_view_call": writer["view_call"],
                "writer_view": hex(writer["view"]),
                "writer_camera": hex(camera["object"]) if camera else None,
                "writer_camera_vtable": hex(camera["vtable"]) if camera else None,
                "opcode": hex(read["opcode"]),
                "payload": hex(read["payload"])}

    view_packets = {(kind, thread, row["ordinal"]): row["header_physical"]
                    for kind in ("semantic packet", "direct packet")
                    for _, thread, row in events[kind]
                    if row["frame"] == source_frame}
    tracked_headers = set()
    for _, thread, bucket in events["track bucket entry"]:
        if bucket["frame"] != source_frame:
            continue
        for kind, label in (("semantic packet", "semantic"),
                            ("direct packet", "direct")):
            tracked_headers.update(view_packets[kind, thread, ordinal]
                                   for ordinal in range(
                                       bucket["first_" + label],
                                       bucket["last_" + label] + 1))
    assert tracked_headers or allow_missing_view_trace
    worker_scopes = {(row["stream"], row["queue"]): row
                     for _, _, row in events["deferred worker end"]
                     if row["frame"] == source_frame}
    if worker_scopes:
        begins = {(row["stream"], row["queue"]): row
                  for _, _, row in events["deferred worker begin"]
                  if row["frame"] == source_frame}
        assert set(begins) == set(worker_scopes)
        assert all(begins[key]["first_packet"] == end["first_packet"]
                   for key, end in worker_scopes.items())
    if allow_missing_view_trace and not tracked_headers:
        assert worker_scopes, "missing both view and worker ownership traces"

    targets = collections.Counter()
    source_callers = collections.Counter()
    source_packets = collections.Counter()
    devices = set()
    entry_arrays = set()
    worker_streams = set()
    worker_queues = set()
    worker_commands = set()
    worker_command_draws = collections.Counter()
    for _, fetch in consumers:
        draw = prepared[fetch["draw"]][1]
        assert draw["packet_physical"] not in tracked_headers
        packet_position, source = source_for(draw)
        if require_command_writers:
            address = source["worker_command_physical"]
            command_writers[address] = writer_for(packet_position, source)
        if worker_scopes:
            scope = worker_scopes[source["worker_stream"],
                                  source["worker_queue"]]
            assert scope["first_packet"] <= source["ordinal"] <= scope[
                "last_packet"]
        source_callers[(source["frame"], source["caller_lr"],
                        source["queued_caller_lr"])] += 1
        source_packets[source["header_physical"]] += 1
        devices.add(source["device"])
        entry_arrays.add(source["entry_array"])
        worker_streams.add(source.get("worker_stream", 0))
        worker_queues.add(source.get("worker_queue", 0))
        worker_commands.add(source.get("worker_command_physical", 0))
        worker_command_draws[source.get("worker_command_physical", 0)] += 1
        targets[(draw["surface_info"], tuple(draw["color_info"]),
                 draw["depth_info"], draw["render_target_bits"])] += 1
    assert len(source_callers) == len(targets) == 1
    assert next(iter(source_callers)) == (source_frame, 0x829F6308, 0)
    return {"source_frame": source_frame, "backend_frame": backend_frame,
            "cube_base": hex(base), "face_copy_ordinals": [
                row["ordinal"] for _, row in faces],
            "cube_descriptor": {"format": next(iter(descriptors))[0],
                                "mip_address": hex(next(iter(descriptors))[1])},
            "consumer_draws": len(consumers),
            "consumer_primary_packets": len(source_packets),
            "consumer_devices": [hex(device) for device in sorted(devices)],
            "consumer_entry_arrays": [hex(address) for address in sorted(entry_arrays)],
            "consumer_worker_streams": [hex(address) for address in sorted(worker_streams)],
            "consumer_worker_queues": [hex(address) for address in sorted(worker_queues)],
            "consumer_worker_commands": [hex(address) for address in sorted(worker_commands)],
            "consumer_worker_command_draws": {
                hex(address): count for address, count in sorted(worker_command_draws.items())},
            "consumer_command_writers": [command_writers[address]
                                         for address in sorted(command_writers)],
            "consumer_source": [{"frame": key[0], "caller_lr": hex(key[1]),
                                 "queued_caller_lr": hex(key[2]), "draws": count}
                                for key, count in source_callers.items()],
            "consumer_targets": [{"surface_info": key[0],
                                  "color_info": key[1], "depth_info": key[2],
                                  "bound_bits": key[3], "draws": count}
                                 for key, count in targets.items()],
            "tracked_view_packet_overlap": (0 if tracked_headers else None)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--backend-frame", type=int, required=True)
    parser.add_argument("--allow-missing-view-trace", action="store_true")
    parser.add_argument("--require-command-writers", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame, args.backend_frame,
                            args.allow_missing_view_trace,
                            args.require_command_writers),
                     indent=2))
