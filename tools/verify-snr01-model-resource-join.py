#!/usr/bin/env python3
"""Join selected procedural model resources to title lists and backend draws."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()

    active = {}
    lists = {}
    resources = []
    model_scopes = packets = 0
    for line in args.log.open(encoding="utf-8"):
        if "FH1 SNR01 " not in line or "{" not in line:
            continue
        match = re.search(r"\[t(\d+)\]", line)
        if not match:
            continue
        thread = int(match.group(1))
        row = json.loads(line[line.index("{"):])
        if row.get("frame") != args.source_frame:
            continue
        if "FH1 SNR01 second track dispatch " in line:
            assert thread not in active
            active[thread] = (row, None)
            model_scopes += row["target"] == 0x82417BC0
        elif "FH1 SNR01 procedural model resource " in line:
            assert thread in active and active[thread][0]["target"] == 0x82417BC0
            assert row["vtable"] == 0x820019CC and row["ready"] == 1
            active[thread] = (active[thread][0], row)
            resources.append(row)
        elif "FH1 SNR01 scene indirect packet " in line and thread in active:
            scope, resource = active[thread]
            if scope["target"] == 0x82417BC0 and resource and row["view_call"] == 8:
                assert row["flush_owner"] == scope["arg6"] + 0xE940
                key = row["target_physical"]
                value = (resource["resource"], row["list_object"])
                assert key not in lists or lists[key] == value
                lists[key] = value
                packets += 1
        elif "FH1 SNR01 track bucket entry " in line and thread in active:
            assert active[thread][0]["bucket_entry"] == row["ordinal"]
            del active[thread]
    assert not active

    ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
    state_draws = [row for row in ledger["draws"]
                   if row["target"].startswith("14020500/")
                   and row["classification"] == "view_owner"
                   and row["flush_caller_lr"] == 0x824170BC]
    assert ledger["backend_frame"] == args.source_frame + 1
    assert all(row["scene_source_frame"] == args.source_frame
               for row in state_draws)
    joined = [row for row in state_draws
              if row["execution_command_buffer"] in lists]
    assert {row["execution_command_buffer"] for row in joined} == set(lists)
    groups = Counter((lists[row["execution_command_buffer"]], row["target"].split("/")[1])
                     for row in joined)
    print(json.dumps({
        "source_frame": args.source_frame,
        "model_dispatches": model_scopes,
        "resource_calls": len(resources),
        "resources": len({row["resource"] for row in resources}),
        "joined_title_packets": packets,
        "joined_lists": len(lists),
        "joined_prepared_draws": len(joined),
        "shared_state_prepared_draws": len(state_draws),
        "groups": [{"resource": f"{resource:08X}", "list": f"{list_object:08X}",
                    "color_word": color, "draws": count}
                   for ((resource, list_object), color), count in sorted(groups.items())],
    }, indent=2))


if __name__ == "__main__":
    main()
