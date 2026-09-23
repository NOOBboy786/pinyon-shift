"""Join selected procedural draw packets to bounded title record payloads."""

import collections
import json
from pathlib import Path
import re
import sys


CANDIDATE = {
    "14020500/00030000/00010400/00000003",
    "14020500/000C0000/00010400/00000003",
}


def verify(log: Path, ledger: Path, require_snapshots: bool = False) -> dict:
    ledger_data = json.loads(ledger.read_text())
    backend_frame = ledger_data["backend_frame"]
    items, payloads = {}, {}
    prepared, vertices, textures = {}, collections.defaultdict(list), collections.defaultdict(list)
    for line in log.read_text(encoding="utf-8-sig").splitlines():
        for marker, destination in (("FH1 SNR01 procedural item ", items),
                                    ("FH1 SNR02 item payload ", payloads)):
            if marker not in line:
                continue
            row = json.loads(line.split(marker, 1)[1])
            key = row["frame"], row["call"]
            assert key not in destination, key
            destination[key] = row
        for marker, destination in (("FH1 SNR01 prepared draw ", prepared),
                                    ("FH1 SNR01 prepared vertex fetch ", vertices),
                                    ("FH1 SNR01 prepared texture fetch ", textures)):
            if marker not in line:
                continue
            row = json.loads(line.split(marker, 1)[1])
            key = row["ordinal"] if destination is prepared else row["draw"]
            if row["frame"] != backend_frame:
                continue
            if destination is prepared:
                assert key not in destination, key
                destination[key] = row
            else:
                destination[key].append(row)
    assert payloads and set(payloads) <= set(items)
    for key, payload in payloads.items():
        item = items[key]
        assert item["descriptor_seen"] and item["runtime_seen"]
        assert (payload["descriptor"], payload["runtime"], payload["kind"]) == (
            item["descriptor_address"], item["runtime_address"],
            item["descriptor_kind"])
        assert re.fullmatch(r"[0-9A-F]{184}", payload["descriptor_words"])
        assert re.fullmatch(r"[0-9A-F]{136}", payload["runtime_words"])
        assert int(payload["descriptor_words"][72:80], 16) == payload["kind"]
    draws = [row for row in ledger_data["draws"]
             if row["target"] in CANDIDATE and
             row["title_packet_caller_lr"] == 0x82415D1C]
    selected = {(row["title_packet_source_frame"], row["title_item_call"])
                for row in draws}
    assert draws and selected <= set(payloads)
    assert all(items[key]["submit_seen"] for key in selected)
    footprints = collections.Counter()
    geometry_by_call = collections.defaultdict(set)
    snapshots = collections.Counter()
    snapshot_bytes = 0
    for row in draws:
        ordinal = row["ordinal"]
        draw = prepared[ordinal]
        vertex = vertices[ordinal]
        texture = textures[ordinal]
        assert draw["packet_physical"] == row["packet_physical"]
        assert draw["indirect_execution"] == row["execution"]
        assert draw["vertex_shader"] == row["vertex_shader"]
        assert draw["index_buffer_type"] == 0 and draw["guest_primitive_type"] == 13
        assert len(vertex) == draw["vertex_fetch_count"] == 1
        assert len(texture) == draw["texture_fetch_count"]
        fetch = vertex[0]
        assert fetch["packet_physical"] == draw["packet_physical"]
        assert (fetch["fetch_constant"], fetch["stride_words"], fetch["type"]) == (95, 10, 3)
        assert fetch["length"] == draw["index_count"] * 10
        snapshots[fetch["cpu_snapshot_status"]] += 1
        if require_snapshots:
            assert fetch["cpu_snapshot_status"] == 1 and fetch["cpu_snapshot_hash"]
            snapshot_bytes += fetch["length"]
        assert fetch["source_execution_0"] == row["execution"]
        assert all(t["packet_physical"] == draw["packet_physical"] for t in texture)
        signature = tuple((t["fetch_constant"], t["format"]) for t in texture)
        assert signature in (((0, 20),), ((0, 20), (13, 6)))
        call = row["title_packet_source_frame"], row["title_item_call"]
        kind = payloads[call]["kind"]
        footprints[(kind, draw["vertex_shader"], draw["pixel_shader"], signature)] += 1
        geometry_by_call[call].add((fetch["guest_base"], fetch["length"],
                                    fetch["cpu_snapshot_hash"]))
    assert len(geometry_by_call) == len(selected)
    if require_snapshots:
        assert all(len(ranges) == 1 for ranges in geometry_by_call.values())
    by_runtime = collections.defaultdict(list)
    for payload in payloads.values():
        by_runtime[payload["runtime"]].append(payload)
    changed_words = collections.Counter()
    changed_pointers = 0
    for samples in by_runtime.values():
        values = [sample["runtime_words"] for sample in samples]
        if len(set(values)) <= 1:
            continue
        changed_pointers += 1
        for word in range(17):
            if len({value[word * 8:word * 8 + 8] for value in values}) > 1:
                changed_words[word] += 1
    return {"selected_draws": len(draws), "selected_calls": len(selected),
            "payloads": len(payloads), "kinds": dict(sorted(collections.Counter(
                payloads[key]["kind"] for key in selected).items())),
            "unique_geometry_ranges": len({geometry[:2]
                                           for ranges in geometry_by_call.values()
                                           for geometry in ranges}),
            "unique_snapshot_hashes": len({geometry[2]
                                          for ranges in geometry_by_call.values()
                                          for geometry in ranges if geometry[2]}),
            "geometry_ranges_per_call": dict(sorted(collections.Counter(
                len(ranges) for ranges in geometry_by_call.values()).items())),
            "vertex_snapshot_statuses": dict(sorted(snapshots.items())),
            "vertex_snapshot_bytes": snapshot_bytes,
            "prepared_footprints": [
                {"kind": kind, "vertex_shader": f"{vs:016X}",
                 "pixel_shader": f"{ps:016X}", "textures": signature, "draws": count}
                for (kind, vs, ps, signature), count in sorted(footprints.items())],
            "reused_runtime_pointers_with_changes": changed_pointers,
            "changed_runtime_words": dict(sorted(changed_words.items()))}


if __name__ == "__main__":
    assert len(sys.argv) in (3, 4), "usage: verify-snr02-item-payload.py LOG LEDGER [--require-vertex-snapshots]"
    assert len(sys.argv) == 3 or sys.argv[3] == "--require-vertex-snapshots"
    print(json.dumps(verify(Path(sys.argv[1]), Path(sys.argv[2]), len(sys.argv) == 4),
                     sort_keys=True))
