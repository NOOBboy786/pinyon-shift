#!/usr/bin/env python3
"""Join selected vegetation packets to final draw topology and constants."""

import argparse
import collections
import json
import math
from pathlib import Path
import struct


def verify(path, frame, require_camera_match=False, require_final_state=False,
           reference_size=None):
    lines = path.read_text(encoding="utf-8").splitlines()
    items = [json.loads(line.split("FH1 SNR03 item ", 1)[1])
             for line in lines if "FH1 SNR03 item {" in line]
    assert items and all(item["frame"] == frame for item in items)
    by_packet = {item["packet_physical"]: item for item in items}
    assert len(by_packet) == len(items)
    bindings = [json.loads(line.split("FH1 scene binding ", 1)[1])
                for line in lines if "FH1 scene binding {" in line]
    selected = [row for row in bindings if row["packet_physical"] in by_packet]
    assert selected and {row["packet_physical"] for row in selected} == set(by_packet)
    final_by_key = {}
    if require_final_state:
        final = [json.loads(line.split("FH1 SNR03 final draw state ", 1)[1])
                 for line in lines if "FH1 SNR03 final draw state {" in line]
        final_by_key = {(row["packet"], row["dynamic"]): row for row in final}
        assert len(final_by_key) == len(final)
        assert {packet for packet, _ in final_by_key} == set(by_packet)
        assert set(final_by_key) == {
            (row["packet_physical"], row["dynamic"]) for row in selected}
        assert all(row["frame"] == frame + 1 for row in final)
        assert all(all(len(row[name]) == 4 for name in (
            "system0", "system1", "system8", "system9", "fetch47"))
                   for row in final)
    viewport_scales = collections.Counter()
    if reference_size:
        assert require_final_state
        width, height = reference_size
        assert width > 0 and height > 0
        word_float = lambda word: struct.unpack("<f", struct.pack("<I", word))[0]
        for row in final_by_key.values():
            scale = list(map(word_float, row["system8"][:3]))
            offset = list(map(word_float, row["system9"][:3]))
            assert scale[0] == 1.0 and scale[1] >= 1.0 and scale[2] == -1.0
            assert math.isclose(offset[0], 1 / width, abs_tol=1e-6)
            assert offset[2] == 1.0
            assert math.isclose((offset[1] + 1) / scale[1] - 1,
                                -1 / height, abs_tol=1e-6)
            viewport_scales[round(scale[1], 6)] += 1
    camera = None
    if require_camera_match:
        camera_rows = [json.loads(line.split("FH1 SNR03 camera row ", 1)[1])
                       for line in lines if "FH1 SNR03 camera row {" in line]
        assert len(camera_rows) == 8
        assert {(row["offset"], row["row"]) for row in camera_rows} == {
            (offset, index) for offset in (80, 144) for index in range(4)}
        assert all(row["frame"] == frame for row in camera_rows)
        camera = [word for row in sorted(
            (row for row in camera_rows if row["offset"] == 144),
            key=lambda row: row["row"]) for word in row["words"]]
    owner_constants = collections.defaultdict(set)
    packet_constants = collections.defaultdict(set)
    packet_vertex_constants = collections.defaultdict(set)
    repeats = collections.Counter()
    for row in selected:
        item = by_packet[row["packet_physical"]]
        assert row["frame"] == frame + 1
        assert row["vertex_shader"] == "5834939992FFC765"
        assert row["pixel_shader"] == "C2F1242C2535A57E"
        assert row["attachment"] == "84241CB4C5BD3DC8"
        assert row["index_base"] == row["index_length"] == 0
        assert row["index_count"] > 0 and row["index_count"] % 4 == 0
        fetch = row["vertices"].rstrip(";").split(":")
        assert len(fetch) == 3 and fetch[:2] == ["95", "4"]
        assert int(fetch[2][:8], 16) & 0x1FFFFFFC == item["vertex_address"] & 0x1FFFFFFC
        assert int(fetch[2][8:], 16) & 0x03FFFFFC == item["vertex_size"] & 0x03FFFFFC
        if final_by_key:
            assert final_by_key[(row["packet_physical"], row["dynamic"])]["fetch47"][2:] == [
                int(fetch[2][:8], 16), int(fetch[2][8:], 16)]
        assert row["index_count"] * 4 == (item["vertex_size"] & 0x03FFFFFC)
        constants = {int(key): value for part in row["constants"].split(";")
                     if ":" in part and part[0].isdigit()
                     for key, value in [part.split(":", 1)]}
        if camera is not None:
            words = {key: tuple(int(value[i:i + 8], 16)
                                for i in range(0, 32, 8))
                     for key, value in constants.items() if len(value) == 32}
            assert words[17028] == tuple(camera[8:12])
            assert words[17016] == tuple(camera[12:16])
            for column, register in enumerate((17356, 17360, 17364)):
                assert words[register][:3] == tuple(camera[4 * row + column]
                                                    for row in range(3))
        assert constants[17396].startswith("3E80000040800000")
        pair = (constants[17020], constants[17024])
        owner_constants[item["owner"]].add(pair)
        packet_constants[row["packet_physical"]].add(pair)
        vertex_constants = tuple(sorted((key, value) for key, value in constants.items()
                                        if 16896 <= key < 17920))
        assert len(vertex_constants) == 24
        packet_vertex_constants[row["packet_physical"]].add(vertex_constants)
        repeats[row["packet_physical"]] += 1
    assert all(len(values) == 1 for values in owner_constants.values())
    assert all(len(values) == 1 for values in packet_constants.values())
    assert all(len(values) == 1 for values in packet_vertex_constants.values())
    assert len({next(iter(values)) for values in owner_constants.values()}) == len(owner_constants)
    assert not any("FH1 SNR03 geometry rejected" in line for line in lines)
    consumed = [line for line in lines
                if "FH1 SNR03 geometry consumed output_frame=" in line]
    assert len(consumed) == 1
    assert f"output_frame={frame + 1} source_frame={frame}" in consumed[0]
    assert f"items={len(items)}" in consumed[0]
    assert "draw_constants=24" in consumed[0]
    if require_final_state:
        assert "system_words=40 fetch_words=4" in consumed[0]
        assert f"final_variants={len(final_by_key)}" in consumed[0]
    return {
        "source_frame": frame,
        "selected_packets": len(items),
        "prepared_bindings": len(selected),
        "owner_constant_pairs": len(owner_constants),
        "vertex_constant_registers_per_packet": 24,
        "repeat_distribution": dict(sorted(collections.Counter(repeats.values()).items())),
        "unselected_probe_bindings": len(bindings) - len(selected),
        "camera144_matches_selected_bindings": len(selected) if camera else None,
        "final_draw_states": len(final_by_key) if require_final_state else None,
        "viewport_scale_y": dict(sorted(viewport_scales.items())) if reference_size else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--source-frame", type=int, default=6000)
    parser.add_argument("--require-camera-match", action="store_true")
    parser.add_argument("--require-final-state", action="store_true")
    parser.add_argument("--reference-size", help="verify full-view remap, e.g. 1280x720")
    args = parser.parse_args()
    size = tuple(map(int, args.reference_size.split("x"))) if args.reference_size else None
    print(json.dumps(verify(args.log, args.source_frame,
                            args.require_camera_match,
                            args.require_final_state, size), sort_keys=True))


if __name__ == "__main__":
    main()
