#!/usr/bin/env python3
"""Verify one bounded track bucket -> PM4 packet -> backend draw capture."""

import argparse
import collections
import json
import re
from pathlib import Path


EVENT = re.compile(r"\[t(\d+)\] FH1 SNR01 (.*?) (\{.*\})")


def verify(path: Path, source_frame: int, backend_frame: int,
           first_model_vtable: int | None = None) -> dict:
    events = collections.defaultdict(list)
    active_views = collections.defaultdict(list)
    for line in path.open(encoding="utf-8-sig", errors="replace"):
        match = EVENT.search(line)
        if match:
            thread, kind = int(match[1]), match[2]
            row = json.loads(match[3])
            if row["frame"] in (source_frame, backend_frame):
                events[kind].append((thread, row))
                if row["frame"] == source_frame:
                    if kind == "view begin":
                        active_views[thread].append(row["view"])
                    elif kind == "view end":
                        assert active_views[thread].pop() == row["view"]
                    elif kind == "track bucket entry":
                        assert active_views[thread][-1] == row["view"]
    assert all(not stack for stack in active_views.values()), "view scope is unfinished"

    entries = [(thread, row) for thread, row in events["track bucket entry"]
               if row["frame"] == source_frame]
    summaries = [row for _, row in events["summary"]
                 if row["frame"] == source_frame]
    assert len(summaries) == 1 and entries, "source capture is incomplete"
    summary = summaries[0]
    assert summary["track_bucket_entries"] == len(entries) < summary["scope_limit"]
    assert not summary["unfinished_track_bucket_scopes"]
    assert not summary["unmatched_track_bucket_exits"]
    assert [row["ordinal"] for _, row in entries] == list(range(1, len(entries) + 1))

    views = {row["view"] for _, row in entries}
    presenters = {row["presenter"] for _, row in entries}
    assert len(views) == len(presenters) == 1, "multiple view/presenter identities"
    view, presenter = next(iter(views)), next(iter(presenters))
    slots = [row for _, row in events["track presentation"]
             if row["frame"] == source_frame and row["slot"] == 75]
    assert slots and all(row["receiver"] == presenter and row["arg9"] == view
                         for row in slots), "slot-75 relationship differs"
    bucket_indices = {5 * row["arg5"] + row["arg6"] for row in slots}

    packets = {}
    for kind in ("semantic packet", "direct packet"):
        packets[kind] = {(thread, row["ordinal"]): row
                         for thread, row in events[kind]
                         if row["frame"] == source_frame}
    draws = collections.Counter(row["packet_physical"]
                                for _, row in events["prepared draw"]
                                if row["frame"] == backend_frame)
    assert draws, "backend draw capture is missing"

    claimed = set()
    physical_headers = set()
    counts = collections.Counter()
    for thread, row in entries:
        assert row["bucket"] == presenter + 56808 + 16 * (
            (row["bucket"] - presenter - 56808) // 16)
        assert (row["bucket"] - presenter - 56808) // 16 in bucket_indices
        first = bool(row["record"])
        assert first != bool(row["secondary_seen"]), "record path is ambiguous"
        assert first or row["secondary_record"], "selected record is null"
        path_name = "first" if first else "second"
        counts[path_name + "_entries"] += 1
        if first_model_vtable is not None:
            if first:
                assert row["first_object"] and row["first_vtable"] == first_model_vtable
                assert row["first_guard"] in (0, 1)
                counts["first_guard_passed"] += row["first_guard"] == 1
            else:
                assert row["secondary_resolved_seen"] and row["auxiliary_seen"]
                counts["second_resolved"] += bool(row["secondary_resolved"])
                counts["second_auxiliary_records"] += bool(row["auxiliary_record"])
        produced = 0
        for kind, label in (("semantic packet", "semantic"),
                            ("direct packet", "direct")):
            start, end = row["first_" + label], row["last_" + label]
            assert end >= start - 1, "invalid packet range"
            for ordinal in range(start, end + 1):
                key = (kind, thread, ordinal)
                assert key not in claimed, "packet belongs to multiple entries"
                claimed.add(key)
                packet = packets[kind].get((thread, ordinal))
                assert packet is not None, "packet ordinal is missing"
                physical_headers.add(packet["header_physical"])
                callbacks = draws[packet["header_physical"]]
                assert callbacks, "record packet has no backend draw"
                counts[path_name + "_packets"] += 1
                counts[path_name + "_draw_callbacks"] += callbacks
                produced += 1
        counts[path_name + "_producing_entries"] += bool(produced)
    assert len(physical_headers) == len(claimed), "packet header address reused"

    return {
        "source_frame": source_frame,
        "backend_frame": backend_frame,
        "view": hex(view),
        "presenter": hex(presenter),
        "entries": len(entries),
        "packet_headers": len(physical_headers),
        **dict(sorted(counts.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    parser.add_argument("--backend-frame", type=int, required=True)
    parser.add_argument("--first-model-vtable", type=lambda value: int(value, 0))
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame, args.backend_frame,
                            args.first_model_vtable), indent=2))


if __name__ == "__main__":
    main()
