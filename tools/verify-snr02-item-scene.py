"""Verify the owned procedural-item frame fixture against its title/GPU trace."""

import collections
import json
from pathlib import Path
import struct
import sys


CANDIDATE = {
    "14020500/00030000/00010400/00000003",
    "14020500/000C0000/00010400/00000003",
}


def hash_bytes(data: bytes) -> int:
    value = 14695981039346656037
    for byte in data:
        value = ((value ^ byte) * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return value


def verify(fixture: Path, log: Path, ledger: Path) -> dict:
    census = json.loads(ledger.read_text())
    source_frame = census["backend_frame"] - 1
    selected = collections.defaultdict(list)
    for row in census["draws"]:
        if row["target"] in CANDIDATE and row["title_packet_caller_lr"] == 0x82415D1C:
            assert row["title_packet_source_frame"] == source_frame
            selected[row["title_item_call"]].append(row)
    assert selected
    title, fetches = {}, {}
    for line in log.read_text(encoding="utf-8-sig").splitlines():
        for marker, destination in (("FH1 SNR02 item payload ", title),
                                    ("FH1 SNR01 prepared vertex fetch ", fetches)):
            if marker not in line:
                continue
            row = json.loads(line.split(marker, 1)[1])
            frame = source_frame if destination is title else census["backend_frame"]
            if row["frame"] != frame:
                continue
            if destination is fetches and (row["fetch_constant"], row["stride_words"]) != (95, 10):
                continue
            key = row["call"] if destination is title else row["draw"]
            assert key not in destination
            destination[key] = row
    data = fixture.read_bytes()
    magic, frame, count = struct.unpack_from("<8sQI", data)
    assert magic == b"SNR02I1\0" and frame == source_frame
    assert count == len(selected) and count <= 512
    camera = struct.unpack_from("<32I", data, 20)
    assert any(camera)
    offset = 148
    calls, total_draws, total_bytes = set(), 0, 0
    for _ in range(count):
        values = struct.unpack_from("<QII23I17I3I", data, offset)
        offset += 188
        call, packet, kind = values[:3]
        descriptor, runtime = values[3:26], values[26:43]
        base, length, draws = values[43:46]
        assert 0 < length <= 256 * 1024 and offset + length <= len(data)
        vertex = data[offset:offset + length]
        offset += length
        assert call in selected and call not in calls
        calls.add(call)
        item = title[call]
        assert kind == item["kind"]
        assert "".join(f"{word:08X}" for word in descriptor) == item["descriptor_words"]
        assert "".join(f"{word:08X}" for word in runtime) == item["runtime_words"]
        assert draws == len(selected[call])
        for row in selected[call]:
            fetch = fetches[row["ordinal"]]
            assert row["packet_physical"] == packet == fetch["packet_physical"]
            assert (fetch["guest_base"], fetch["length"],
                    fetch["cpu_snapshot_status"], fetch["cpu_snapshot_hash"]) == (
                base, length, 1, hash_bytes(vertex))
        total_draws += draws
        total_bytes += length
    assert calls == set(selected) and offset == len(data)
    return {"source_frame": frame, "calls": count, "draws": total_draws,
            "owned_vertex_bytes": total_bytes, "fixture_bytes": len(data)}


if __name__ == "__main__":
    assert len(sys.argv) == 4, "usage: verify-snr02-item-scene.py FIXTURE LOG LEDGER"
    print(json.dumps(verify(*(Path(arg) for arg in sys.argv[1:])), sort_keys=True))
