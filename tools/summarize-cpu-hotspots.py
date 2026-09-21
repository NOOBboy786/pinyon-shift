#!/usr/bin/env python3
"""Rank sampled CPU and wait cost by source frame from normalized WPA exports."""

import argparse
import bisect
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)


def percentile(values, fraction):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * fraction))]


def summarize(markers_path, samples_path, waits_path=None):
    markers = sorted(
        (float(row["timestamp_ms"]), int(row["source_frame"]))
        for row in rows(markers_path)
    )
    if not markers:
        raise ValueError("markers CSV contains no source frames")
    times = [item[0] for item in markers]

    def frame_at(timestamp):
        index = bisect.bisect_right(times, timestamp) - 1
        return markers[index][1] if index >= 0 else None

    frames = defaultdict(lambda: {"cpu_ms": 0.0, "wait_ms": 0.0})
    functions = defaultdict(float)
    modules = defaultdict(float)
    waits = defaultdict(float)
    unmatched = {"samples": 0, "waits": 0}

    for row in rows(samples_path):
        frame = frame_at(float(row["timestamp_ms"]))
        if frame is None:
            unmatched["samples"] += 1
            continue
        cost = float(row["cpu_ms"])
        frames[frame]["cpu_ms"] += cost
        modules[row["module"] or "<unknown>"] += cost
        functions[row["function"] or "<unknown>"] += cost

    if waits_path:
        for row in rows(waits_path):
            frame = frame_at(float(row["timestamp_ms"]))
            if frame is None:
                unmatched["waits"] += 1
                continue
            cost = float(row["wait_ms"])
            frames[frame]["wait_ms"] += cost
            waits[row["wait_reason"] or "<unknown>"] += cost

    def ranked(values):
        return [
            {"name": name, "ms": round(cost, 3)}
            for name, cost in sorted(values.items(), key=lambda item: item[1], reverse=True)
        ]

    cpu = [value["cpu_ms"] for value in frames.values()]
    wait = [value["wait_ms"] for value in frames.values()]
    return {
        "schema": "pinyon-shift.cpu-hotspots.v1",
        "source_frames": len(frames),
        "unmatched_rows": unmatched,
        "per_frame_ms": {
            "cpu_median": round(statistics.median(cpu), 3) if cpu else 0.0,
            "cpu_p95": round(percentile(cpu, 0.95), 3),
            "wait_median": round(statistics.median(wait), 3) if wait else 0.0,
            "wait_p95": round(percentile(wait, 0.95), 3),
        },
        "top_functions": ranked(functions),
        "top_modules": ranked(modules),
        "top_wait_reasons": ranked(waits),
    }


def markdown(report, limit=20):
    timing = report["per_frame_ms"]
    lines = [
        "# CPU hotspot report",
        "",
        f"Frames: {report['source_frames']}",
        f"CPU/frame: median {timing['cpu_median']:.3f} ms, p95 {timing['cpu_p95']:.3f} ms",
        f"Wait/frame: median {timing['wait_median']:.3f} ms, p95 {timing['wait_p95']:.3f} ms",
    ]
    for title, key in (
        ("Functions", "top_functions"),
        ("Modules", "top_modules"),
        ("Wait reasons", "top_wait_reasons"),
    ):
        lines += ["", f"## {title}", "", "| Rank | Name | Total ms |", "|---:|---|---:|"]
        lines += [
            f"| {index} | `{item['name']}` | {item['ms']:.3f} |"
            for index, item in enumerate(report[key][:limit], 1)
        ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("markers", type=Path)
    parser.add_argument("samples", type=Path)
    parser.add_argument("--waits", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = summarize(args.markers, args.samples, args.waits)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text(markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
