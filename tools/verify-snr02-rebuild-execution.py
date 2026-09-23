#!/usr/bin/env python3
"""Verify one event-triggered track rebuild reaches the next backend frame."""

import argparse
import json
from pathlib import Path


def verify(path: Path, view_call: int = 0, require_color: bool = False,
           require_record_control: bool = False) -> dict:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if ("FH1 SNR02 " in line or "FH1 SNR01 track nested entry " in line
                or "FH1 SNR01 track selected record " in line):
            if "{" in line:
                events.append((line[:line.index("{")], json.loads(line[line.index("{"):])))
            else:
                assert "draw limit reached" not in line, "capture exceeded the draw limit"
    captures = [(i, row) for i, (name, row) in enumerate(events) if "rebuild capture " in name]
    assert len(captures) == 1, f"expected one capture, found {len(captures)}"
    capture_index, capture = captures[0]
    frame, target = capture["frame"], capture["command_target"]
    if view_call:
        assert capture.get("view_call") == view_call
    assert frame > 0 and target > 0 and capture["state"] and capture["descriptor"]
    assert capture["flags_address"] == capture["parent"] + 56
    assert capture["mask"] and capture["parent_flags"] & capture["mask"] == 0
    entries, records, flushes, executions, draws = [], [], [], [], []
    ranges, range_words, lookups = [], [], []
    fetches = {}
    for i, (name, row) in enumerate(events):
        if "track nested entry " in name and i > capture_index and row["frame"] == frame:
            if row["flags_address"] != capture["flags_address"]:
                continue
            assert (row["container_vtable"], row["submodel_vtable"], row["entry_vtable"]) == (
                0x820016B4, 0x82001474, 0x8200143C)
            assert row["selected"] == 1
            entries.append(row)
        elif "track selected record " in name and i > capture_index and row["frame"] == frame:
            if row["flags_address"] != capture["flags_address"]:
                continue
            assert entries and len(records) < len(entries)
            entry = entries[len(records)]
            assert all(row[key] == entry[key] for key in ("flags_address", "container", "submodel", "entry", "entry_index"))
            assert row["record"] == row["record_base"] + 56 * row["entry_index"]
            assert len(row["words"]) == 14
            records.append(row)
        elif "rebuild flush " in name:
            assert i > capture_index and row["frame"] == frame
            assert all(row[key] == capture[key] for key in ("state", "descriptor", "command_target"))
            assert row["caller_lr"] == 0x82437048 and records
            flushes.append(row)
        elif "rebuild indirect " in name:
            assert flushes and row["frame"] == frame + 1 and row["command_target"] == target
            assert row["dispatch_packet"] and row["command_bytes"]
            executions.append(row)
        elif "rebuild prepared draw " in name:
            assert executions and row["frame"] == frame + 1 and row["command_target"] == target
            assert row["dispatch_packet"] in {entry["dispatch_packet"] for entry in executions}
            assert row["draw"] == len(draws) + 1 and row["draw_packet"] and row["index_count"]
            assert row["vertex_fetch_count"] <= 32 and row["texture_fetch_count"] <= 32
            draws.append(row)
        elif "rebuild vertex fetch " in name or "rebuild texture fetch " in name:
            assert draws and row["draw"] == draws[-1]["draw"]
            kind = "vertex" if "vertex fetch " in name else "texture"
            fetches[(kind, row["draw"])] = fetches.get((kind, row["draw"]), 0) + 1
        elif "selected mesh range " in name:
            ranges.append(row)
        elif "selected range word " in name:
            range_words.append(row)
        elif "selected resource lookup " in name:
            lookups.append(row)
    assert entries and len(entries) == len(records) and flushes and executions and draws
    if require_color:
        assert any(draw.get("color_mask", 0) and draw["pixel_shader"] for draw in draws), "no color-writing draw"
    control = {}
    if require_record_control:
        assert len(records) == len(ranges) == 1, "expected one captured record and range"
        record, mesh_range = records[0], ranges[0]
        assert record["mask"] == capture["mask"]
        assert mesh_range["record"] == record["record"] and mesh_range["entry"] == record["entry"]
        assert (mesh_range["range_start"], mesh_range["range_end"]) == tuple(record["words"][10:12])
        assert 0 <= mesh_range["range_count"] <= 20
        assert mesh_range["range_end"] - mesh_range["range_start"] == 4 * mesh_range["range_count"]
        assert len(range_words) == mesh_range["range_count"]
        assert all(word["record"] == record["record"] and word["index"] == i
                   for i, word in enumerate(range_words))
        if record["resource_skip_flag"]:
            assert not lookups, "resource lookup logged despite skip flag"
        for lookup in lookups:
            assert lookup["record"] == record["record"] and lookup["index"] == record["words"][0]
            assert lookup["table_entry"] == lookup["resource"]
            assert lookup["field60"] == lookup["argument"]
        control = {"resource_lookup_skipped": record["resource_skip_flag"],
                   "range_skipped": record["range_skip_flag"],
                   "range_values": [word["value"] for word in range_words],
                   "resource_lookups": len(lookups)}
    for draw in draws:
        assert fetches.get(("vertex", draw["draw"]), 0) == draw["vertex_fetch_count"]
        assert fetches.get(("texture", draw["draw"]), 0) == draw["texture_fetch_count"]
    return {"source_frame": frame, "view_call": capture.get("view_call"),
            "backend_frame": frame + 1,
            "command_target": f"0x{target:08X}", "selected_records": len(records),
            "flushes": len(flushes), "indirect_executions": len(executions),
            "prepared_draws": len(draws), "vertex_fetches": sum(
                count for (kind, _), count in fetches.items() if kind == "vertex"),
            "texture_fetches": sum(count for (kind, _), count in fetches.items() if kind == "texture"),
            "pixel_shaders": sorted({draw["pixel_shader"] for draw in draws}),
            "color_masks": sorted({draw["color_mask"] for draw in draws if "color_mask" in draw}),
            **control}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--view-call", type=int, default=0)
    parser.add_argument("--require-color", action="store_true")
    parser.add_argument("--require-record-control", action="store_true")
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.view_call, args.require_color,
                            args.require_record_control), indent=2))
