#!/usr/bin/env python3
"""Check bounded CPU-authoritative fetch-95 evidence for a published scene."""

import argparse
import collections
import json
from pathlib import Path


def verify(path, frame):
    lines = path.read_text(encoding="utf-8").splitlines()
    items = [json.loads(line.split("FH1 SNR03 item ", 1)[1])
             for line in lines if "FH1 SNR03 item {" in line]
    assert items and all(item["frame"] == frame for item in items)
    assert [item["ordinal"] for item in items] == list(range(1, len(items) + 1))
    by_packet = {item["packet_physical"]: item for item in items}
    assert len(by_packet) == len(items)
    published = [i for i, line in enumerate(lines)
                 if f"FH1 SNR03 scene published frame={frame} " in line]
    consumed = [i for i, line in enumerate(lines)
                if f"FH1 SNR03 scene consumed output_frame={frame + 1} source_frame={frame} " in line]
    assert len(published) == len(consumed) == 1
    assert published[0] < consumed[0]
    assert not any("FH1 SNR03 geometry rejected" in line for line in lines)
    geometry = [line for line in lines
                if f"FH1 SNR03 geometry consumed output_frame={frame + 1} source_frame={frame} " in line]
    assert len(geometry) == 1
    assert f"items={len(items)} " in geometry[0]
    owned_bytes = sum(item["vertex_size"] & 0x03FFFFFC for item in items)
    assert f"bytes={owned_bytes} " in geometry[0]
    hashes = collections.defaultdict(set)
    counts = collections.Counter()
    first_fetch = {}
    for position, line in enumerate(lines):
        if "FH1 SNR01 prepared vertex fetch {" not in line:
            continue
        fetch = json.loads(line.split("FH1 SNR01 prepared vertex fetch ", 1)[1])
        packet = fetch["packet_physical"]
        if packet not in by_packet or fetch["frame"] != frame + 1:
            continue
        item = by_packet[packet]
        assert fetch["fetch_constant"] == 95
        assert fetch["stride_words"] == 4
        assert fetch["guest_base"] == item["vertex_address"] & 0x1FFFFFFC
        assert fetch["length"] == item["vertex_size"] & 0x03FFFFFC
        assert fetch["type"] == item["vertex_address"] & 3 == 3
        assert fetch["cpu_snapshot_status"] == 1, (packet, fetch["cpu_snapshot_status"])
        assert fetch["cpu_snapshot_hash"] != 0
        assert position < consumed[0], packet
        first_fetch.setdefault(packet, position)
        hashes[packet].add(fetch["cpu_snapshot_hash"])
        counts[packet] += 1
    assert set(hashes) == set(by_packet), (len(hashes), len(by_packet))
    assert all(len(values) == 1 for values in hashes.values())
    assert sum(counts.values()) >= len(items)
    return {
        "source_frame": frame,
        "output_frame": frame + 1,
        "items": len(items),
        "owned_vertex_bytes": owned_bytes,
        "prepared_fetches": sum(counts.values()),
        "cpu_snapshot_bytes": sum((item["vertex_size"] & 0x03FFFFFC) * counts[packet]
                                  for packet, item in by_packet.items()),
        "first_selected_fetch_before_title_publication": min(first_fetch.values()) < published[0],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, default=6000)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.source_frame), sort_keys=True))


if __name__ == "__main__":
    main()
