#!/usr/bin/env python3
"""Check the bounded title-view draw -> D3D12 attachment -> copy sequence."""

import argparse
import collections
import json
import re
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (.*?) (\{.*\})")


def raw_target(row):
    return row["surface_info"], tuple(row["color_info"]), row["depth_info"]


def verify(path: Path, source_frame: int, backend_frame: int):
    events = collections.defaultdict(list)
    backend_order = []
    for line in path.open(encoding="utf-8-sig", errors="replace"):
        match = EVENT.search(line)
        if not match:
            continue
        thread, kind, row = int(match[1]), match[2], json.loads(match[3])
        if row["frame"] == source_frame:
            events[kind].append((thread, row))
        if row["frame"] == backend_frame and kind in ("prepared draw", "copy"):
            backend_order.append((kind, row))

    views = [row for _, row in events["view begin"]]
    assert len(views) == 8 and len(events["view end"]) == 8
    tracks = {(thread, row["call"]): row["view_call"]
              for thread, row in events["track presentation"]
              if row["slot"] == 75}
    assert len(tracks) == 19
    packets = {(kind, thread, row["ordinal"]): row["header_physical"]
               for kind in ("semantic packet", "direct packet")
               for thread, row in events[kind]}
    header_views = {}
    for thread, bucket in events["track bucket entry"]:
        view_call = tracks[thread, bucket["track_call"]]
        for kind, label in (("semantic packet", "semantic"),
                            ("direct packet", "direct")):
            for ordinal in range(bucket["first_" + label],
                                 bucket["last_" + label] + 1):
                header = packets[kind, thread, ordinal]
                assert header not in header_views
                header_views[header] = view_call

    view_events = collections.defaultdict(list)
    for position, (kind, row) in enumerate(backend_order):
        if kind != "prepared draw":
            continue
        view_call = header_views.get(row["packet_physical"])
        if view_call is not None:
            view_events[view_call].append((position, row))
    assert set(view_events) == {row["call"] for row in views}

    copies = [(position, row) for position, (kind, row) in
              enumerate(backend_order) if kind == "copy"]
    assert copies and all(row["succeeded"] for _, row in copies)
    result = []
    for index, view in enumerate(views):
        selected = view_events[view["call"]]
        targets = collections.Counter(raw_target(row) for _, row in selected)
        after = selected[0][0] - 1 if index == 7 else selected[-1][0]
        before = (view_events[views[index + 1]["call"]][0][0]
                  if index + 1 < len(views) else len(backend_order))
        copied = [(position, row) for position, row in copies
                  if after < position < before and raw_target(row) in targets]
        if index == 0:
            assert len(targets) == 1 and len(selected) == 74
            assert all(row["render_target_bits"] == 1 for _, row in selected)
            assert any((row["resolve_width"], row["resolve_height"])
                       == (1280, 720) for _, row in copied)
        elif index < 7:
            assert len(targets) == 1 and len(copied) == 1
            assert all(row["render_target_bits"] == 3 for _, row in selected)
            assert (copied[0][1]["resolve_width"],
                    copied[0][1]["resolve_height"]) == (256, 256)
            assert copied[0][1]["written_length"] == 256 * 256 * 4
        else:
            assert len(targets) == 2 and len(selected) > 300
            assert all(row["render_target_bits"] == 3 for _, row in selected)
            assert len(copied) == 12
            assert len({raw_target(row) for _, row in copied}) == 1
        result.append({"view_call": view["call"], "draws": len(selected),
                       "targets": [{"raw": target, "draws": count}
                                   for target, count in targets.items()],
                       "matched_copies": [row["ordinal"] for _, row in copied],
                       "copy_destinations": [row["dest_base"] for _, row in copied]})
    face_destinations = [row["copy_destinations"][0] for row in result[1:7]]
    cube_base = min(face_destinations)
    face_bytes = 256 * 256 * 4
    assert [(address - cube_base) // face_bytes
            for address in face_destinations] == [0, 4, 2, 1, 3, 5]
    assert all((address - cube_base) % face_bytes == 0
               for address in face_destinations)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--backend-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame, args.backend_frame),
                     indent=2))
