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


def verify(path: Path, source_frame: int, backend_frame: int):
    events = collections.defaultdict(list)
    for line_number, line in enumerate(path.open(encoding="utf-8-sig",
                                                  errors="replace")):
        match = EVENT.search(line)
        if match:
            row = json.loads(match[3])
            if row["frame"] in (source_frame, backend_frame):
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
    primary = {row["header_physical"]: row for _, _, row in
               events["primary indirect packet"]
               if row["frame"] == source_frame}
    assert dispatches and primary

    def source_for(draw):
        execution = draw["indirect_execution"]
        while dispatches[execution]["parent"]:
            execution = dispatches[execution]["parent"]
        return primary[dispatches[execution]["dispatch_packet_physical"]]

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
    assert tracked_headers

    targets = collections.Counter()
    source_callers = collections.Counter()
    for _, fetch in consumers:
        draw = prepared[fetch["draw"]][1]
        assert draw["packet_physical"] not in tracked_headers
        source = source_for(draw)
        source_callers[(source["frame"], source["caller_lr"],
                        source["queued_caller_lr"])] += 1
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
            "consumer_source": [{"frame": key[0], "caller_lr": hex(key[1]),
                                 "queued_caller_lr": hex(key[2]), "draws": count}
                                for key, count in source_callers.items()],
            "consumer_targets": [{"surface_info": key[0],
                                  "color_info": key[1], "depth_info": key[2],
                                  "bound_bits": key[3], "draws": count}
                                 for key, count in targets.items()],
            "tracked_view_packet_overlap": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--backend-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame, args.backend_frame),
                     indent=2))
