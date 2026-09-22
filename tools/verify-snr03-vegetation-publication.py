#!/usr/bin/env python3
"""Verify one owned title vegetation snapshot reaches its exact output frame."""

import argparse
import collections
import hashlib
import json
import re
from pathlib import Path


PUBLISHED = re.compile(
    r"FH1 SNR03 scene published frame=(\d+) view=(\d+) camera=(\d+) "
    r"items=(\d+) fingerprint=(\d+)")
CONSUMED = re.compile(
    r"FH1 SNR03 scene consumed output_frame=(\d+) source_frame=(\d+) "
    r"view=(\d+) camera=(\d+) items=(\d+) fingerprint=(\d+)")
ITEM = "FH1 SNR03 item "
FIELDS = {
    "owner": "title_second_draw_vegetation_owner",
    "record": "title_second_draw_bound_record",
    "vertex_descriptor": "title_second_draw_vertex_descriptor",
    "vertex_address": "title_second_draw_vertex_address",
    "vertex_size": "title_second_draw_vertex_size",
    "bucket_entry": "title_second_draw_bucket_entry",
}


def verify(log_path, ledger_path, source_frame):
    published, consumed, items = [], [], []
    view_begins, view_ends = [], []
    with log_path.open(encoding="utf-8", errors="replace") as log:
        for line in log:
            if match := PUBLISHED.search(line):
                if int(match[1]) == source_frame:
                    published.append(tuple(map(int, match.groups())))
            if match := CONSUMED.search(line):
                if int(match[2]) == source_frame:
                    consumed.append(tuple(map(int, match.groups())))
            if ITEM in line:
                item = json.loads(line.split(ITEM, 1)[1])
                if item["frame"] == source_frame:
                    items.append(item)
            for prefix, rows in (("FH1 SNR01 view begin ", view_begins),
                                 ("FH1 SNR01 view end ", view_ends)):
                if prefix in line:
                    row = json.loads(line.split(prefix, 1)[1])
                    if row["frame"] == source_frame and row["call"] == 8:
                        rows.append(row)
            if "FH1 SNR03 scene rejected" in line or \
                    "FH1 SNR03 scene dropped" in line or \
                    "FH1 SNR03 scene missing" in line:
                raise AssertionError(line.strip())
    assert len(published) == len(consumed) == 1
    frame, view, camera, count, fingerprint = published[0]
    output, consumed_frame, consumed_view, consumed_camera, consumed_count, consumed_fingerprint = consumed[0]
    assert (frame, view, camera, count, fingerprint) == (
        consumed_frame, consumed_view, consumed_camera,
        consumed_count, consumed_fingerprint)
    assert output == source_frame + 1 and view and camera and 0 < count <= 512
    assert len(view_begins) == len(view_ends) == 1
    assert view_begins[0]["view"] == view_ends[0]["view"] == view
    assert view_ends[0]["camera"] == camera
    assert sorted(item["ordinal"] for item in items) == list(range(1, count + 1))
    packets = {item["packet_physical"]: item for item in items}
    assert len(packets) == count

    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["source_frames"] == [source_frame, source_frame + 1]
    assert ledger["backend_frame"] == output
    assert ledger["log_sha256"] == hashlib.sha256(log_path.read_bytes()).hexdigest().upper()
    draws = collections.defaultdict(list)
    for row in ledger["draws"]:
        if (row["title_packet_source_frame"] == source_frame and
                row["title_packet_view_call"] == 8 and
                row["title_second_path_caller_lr"] == 0x82413A84):
            assert row["classification"] == "direct_root"
            assert not row["no_attachment_write"]
            draws[row["packet_physical"]].append(row)
    assert set(draws) == set(packets), (
        f"snapshot/draw packet mismatch: {len(packets)} vs {len(draws)}")
    assert [item["packet_physical"] for item in items] == sorted(
        packets, key=lambda packet: draws[packet][0]["title_packet_ordinal"])
    for packet, item in packets.items():
        assert item["owner"] and item["record"] and item["vertex_address"]
        assert item["vertex_size"] and item["vertex_descriptor"]
        for row in draws[packet]:
            for item_field, ledger_field in FIELDS.items():
                assert item[item_field] == row[ledger_field], (
                    f"packet {packet}: {item_field} differs")
    return {
        "source_frame": source_frame,
        "output_frame": output,
        "view": view,
        "camera": camera,
        "items": count,
        "prepared_draw_callbacks": sum(map(len, draws.values())),
        "fingerprint": fingerprint,
        "log_sha256": ledger["log_sha256"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--source-frame", type=int, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.log, args.ledger, args.source_frame), indent=2))


if __name__ == "__main__":
    main()
