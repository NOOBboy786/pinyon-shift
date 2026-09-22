#!/usr/bin/env python3
"""Verify the bounded player-local map-entity pool observation."""

import argparse
import json
from pathlib import Path


def rows(path, label):
    marker = f"FH1 SNR01 {label} "
    return [json.loads(line.split(marker, 1)[1])
            for line in path.open(encoding="utf-8", errors="replace")
            if marker in line]


def verify(path, frame):
    installs = [row for row in rows(path, "vehicle map pool")
                if row["frame"] <= frame]
    samples = [row for row in rows(path, "player map entity")
               if row["frame"] == frame]
    assignments = rows(path, "player vehicle ID assigned")
    assert installs and len(samples) == 1
    install, sample = installs[-1], samples[0]
    assert sample["pool"] == install["pool"]
    assert sample["entity"] == sample["pool"] + 32
    assert sample["vtable"] == install["player_vtable"] == 0x8201D380
    assert sample["vehicle_id"] == install["player_vehicle_id"] == 0xFFFFFFFF
    assert not [row for row in assignments if row["entity"] == sample["entity"]]
    assert all(sample[key] == 0 for key in ("link72", "link76", "link84"))
    return {"frame": frame, "pool_installs": len(installs),
            "player_entity": hex(sample["entity"]),
            "player_vtable": hex(sample["vtable"]),
            "vehicle_id": hex(sample["vehicle_id"]),
            "vehicle_id_assignments": 0,
            "direct_links_nonzero": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame), indent=2))
