#!/usr/bin/env python3
"""Verify a title-side track-model rebuild scope in one source frame."""

import argparse
import collections
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()

    scopes = {}
    counts = collections.Counter()
    instances = set()
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
        if "FH1 SNR01 track model begin " in line:
            assert thread not in scopes
            scopes[thread] = {"instance": row["resource"], "parent": None,
                              "descriptor": None, "gate": None,
                              "entry": None, "records": 0, "packets": 0}
        elif thread in scopes:
            scope = scopes[thread]
            if "FH1 SNR01 track model ready " in line:
                assert row["resource"] == scope["instance"]
                scope["parent"] = row["parent"]
            elif "FH1 SNR01 track descriptor " in line:
                assert row["resource"] == scope["instance"]
                scope["descriptor"] = row["words"][4]
            elif "FH1 SNR01 track rebuild gate " in line:
                flags_address = row.get("flags_address", row.get("instance"))
                assert scope["parent"] and row["parent"] == scope["parent"]
                assert flags_address == scope["parent"] + 56
                scope["gate"] = row["cached_flag"]
            elif "FH1 SNR01 track nested entry " in line:
                flags_address = row.get("flags_address", row.get("instance"))
                assert scope["gate"] == 0 and flags_address == scope["parent"] + 56
                assert (row["container_vtable"], row["submodel_vtable"],
                        row["entry_vtable"]) == (0x820016B4, 0x82001474, 0x8200143C)
                assert row["selected"] == 1 and scope["entry"] is None
                scope["entry"] = row
            elif "FH1 SNR01 track selected record " in line:
                entry = scope["entry"]
                assert entry is not None
                flags_address = row.get("flags_address", row.get("instance"))
                assert flags_address == scope["parent"] + 56
                assert all(row[key] == entry[key] for key in
                           ("container", "submodel", "entry", "entry_index"))
                assert row["record"] == row["record_base"] + 56 * row["entry_index"]
                assert len(row["words"]) == 14
                scope["entry"] = None
                scope["records"] += 1
            elif ("FH1 SNR01 scene indirect packet " in line and
                  row["view_call"] == 8 and
                  row["flush_caller_lr"] == 0x824170BC):
                assert scope["descriptor"] & 0x1FFFFFFF == row["target_physical"]
                scope["packets"] += 1
            elif "FH1 SNR01 track model end " in line:
                assert scope["entry"] is None
                counts["track_calls"] += 1
                if scope["gate"] == 0:
                    assert scope["records"] > 0
                    counts["rebuild_calls"] += 1
                    counts["selected_records"] += scope["records"]
                    counts["rebuild_packets"] += scope["packets"]
                    instances.add(scope["instance"])
                else:
                    assert scope["records"] == 0
                scopes.pop(thread)
    assert not scopes and counts["rebuild_calls"] and counts["selected_records"]
    print(json.dumps({"source_frame": args.source_frame, **counts,
                      "rebuild_instances": len(instances)}, indent=2))


if __name__ == "__main__":
    main()
