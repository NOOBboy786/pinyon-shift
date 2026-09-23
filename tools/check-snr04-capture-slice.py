#!/usr/bin/env python3
"""Compare an owned SNR-03 fixture's post-VS output with a RenderDoc slice probe."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


def check(fixture_path, positions_path, probe_path):
    fixture = fixture_path.read_bytes()
    positions = positions_path.read_bytes()
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    assert fixture[:8] == b"SNR03F1\0" and probe["stage"] == "done"
    item_count = struct.unpack_from("<I", fixture, 24)[0]
    assert 0 < item_count <= 512
    offset = 156
    position_offset = 0
    expected_counts = Counter()
    matched = []
    for ordinal in range(1, item_count + 1):
        assert offset + 48 <= len(fixture), "truncated fixture item"
        *_, vertices, vertex_bytes, constants, variants = struct.unpack_from(
            "<6IQ4I", fixture, offset)
        assert vertices > 0 and vertices % 4 == 0
        assert vertex_bytes == vertices * 4 and constants == 24
        assert 0 < variants <= 4
        expected_counts[vertices] += variants
        offset += 48 + 384 + vertex_bytes + variants * 184
        size = vertices * 16
        digest = hashlib.sha256(positions[position_offset:position_offset + size]).hexdigest()
        matches = [entry["event"] for entry in probe["matches"]
                   if entry["count"] == vertices and entry["postvs"] == digest]
        assert matches, f"item {ordinal} post-VS mismatch"
        matched.append((ordinal, matches[0]))
        position_offset += size
    assert offset == len(fixture) and position_offset == len(positions)
    assert expected_counts == Counter(entry["count"] for entry in probe["matches"])
    assert len(probe["matches"]) == sum(expected_counts.values())
    assert len({event for _, event in matched}) == item_count
    return {"items": item_count, "captured_variants": len(probe["matches"]),
            "matched_first_variants": len(matched),
            "postvs_sha256": hashlib.sha256(positions).hexdigest(),
            "first_event": matched[0][1], "last_event": matched[-1][1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    parser.add_argument("postvs", type=Path)
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.fixture, args.postvs, args.probe), sort_keys=True))


if __name__ == "__main__":
    main()
