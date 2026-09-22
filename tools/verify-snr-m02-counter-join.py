#!/usr/bin/env python3
"""Verify the title counter waits against host PM4 memory writes in one trace."""

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    lines = args.log.read_text(encoding="utf-8", errors="replace").splitlines()
    assert not any("SNRM02" in line and "trace limit reached" in line for line in lines)

    events = []
    pattern = re.compile(r"FH1 SNRM02 (wait|writer|host_store) (\{.*\})")
    for line in lines:
        match = pattern.search(line)
        if match:
            events.append((match[1], json.loads(match[2])))

    waits = [event for kind, event in events if kind == "wait"]
    loops = [event for event in waits if event["entered_loop"]]
    writers = [event for kind, event in events if kind == "writer"]
    stores = [event for kind, event in events if kind == "host_store"]
    assert loops and stores and writers, "trace did not cover all three paths"
    assert all(not event["recoveries"] for event in waits), "counter recovery occurred"
    assert all(not event["expected_title_store"] for event in writers), "title store ran"

    for wait in loops:
        assert wait["published_before"] < wait["requested"] <= wait["published_after"]
        assert any(
            store["path"] == "event_write_shd"
            and store["physical"] == wait["published_physical"]
            and wait["begin_ns"] <= store["time_ns"] <= wait["end_ns"]
            and int.from_bytes(store["value"].to_bytes(4, "little"), "big")
            == wait["requested"]
            for store in stores
        ), f"unmatched wait for {wait['requested']}"

    print(
        json.dumps(
            {
                "waits": len(waits),
                "polling_waits_matched": len(loops),
                "host_stores": len(stores),
                "title_publish_calls": len(writers),
                "polling_wait_ms": round(
                    sum(event["end_ns"] - event["begin_ns"] for event in loops)
                    / 1_000_000,
                    3,
                ),
            }
        )
    )


if __name__ == "__main__":
    main()
