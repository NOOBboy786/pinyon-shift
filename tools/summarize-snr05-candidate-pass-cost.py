#!/usr/bin/env python3
"""Bound candidate-attachment GPU work in an FH1 corpus/SNR-01 trace."""

import argparse
import collections
import json
import re
import statistics
from pathlib import Path


def summarize(lines, backend_frame, start_frame, end_frame, targets):
    attachment_by_target = collections.defaultdict(set)
    attachment_by_family = {}
    samples = collections.defaultdict(list)
    losses = []
    for line in lines:
        if "FH1 SNR01 prepared draw " in line:
            row = json.loads(line.split("FH1 SNR01 prepared draw ", 1)[1])
            if row["frame"] == backend_frame:
                target = "/".join(f"{value:08X}" for value in (
                    row["surface_info"], row["color_info"][0],
                    row["depth_info"], row["render_target_bits"]))
                if target in targets:
                    attachment_by_target[target].add(f'{row["attachment_state"]:016X}')
        elif "FH1 V5 pass family " in line:
            match = re.search(
                r"FH1 V5 pass family ([0-9A-F]{16}): attachment ([0-9A-F]{16})", line)
            if match:
                previous = attachment_by_family.setdefault(match[1], match[2])
                if previous != match[2]:
                    raise ValueError(f"family {match[1]} changed attachment")
        elif "FH1 V5 pass sample " in line:
            row = json.loads(line.split("FH1 V5 pass sample ", 1)[1])
            if start_frame <= row["frame"] <= end_frame:
                samples[row["frame"]].append(row)
        elif "FH1 timing loss reasons " in line:
            losses.append(json.loads(line.split("FH1 timing loss reasons ", 1)[1]))
    if set(attachment_by_target) != targets or not samples or not losses:
        raise ValueError("missing candidate draws, pass samples or loss report")
    if any(any(count for count in row.values()) for row in losses):
        raise ValueError("GPU pass timing losses were reported")

    candidate_attachments = set().union(*attachment_by_target.values())
    frames = []
    for frame, rows in sorted(samples.items()):
        candidate = [row for row in rows if
                     attachment_by_family.get(row["family"]) in candidate_attachments]
        unknown = [row for row in rows if row["family"] not in attachment_by_family]
        frames.append({
            "frame": frame,
            "total_gpu_ms": sum(row["total_ns"] for row in rows) / 1e6,
            "candidate_gpu_ms": sum(row["total_ns"] for row in candidate) / 1e6,
            "unmapped_gpu_ms": sum(row["total_ns"] for row in unknown) / 1e6,
            "candidate_prepare_cpu_ms": sum(row["prepare_cpu_ns"] for row in candidate) / 1e6,
            "candidate_passes": len(candidate),
            "unmapped_passes": len(unknown),
        })
    return {
        "schema": "pinyon-shift.snr05-candidate-pass-cost.v1",
        "backend_frame": backend_frame,
        "candidate_targets": {key: sorted(value) for key, value in sorted(attachment_by_target.items())},
        "loss_reports": len(losses),
        "frames": frames,
        "medians_ms": {
            key: statistics.median(row[key] for row in frames)
            for key in ("total_gpu_ms", "candidate_gpu_ms", "unmapped_gpu_ms",
                        "candidate_prepare_cpu_ms")
        },
        "limits": {
            "attachment_proxy_only": True,
            "unmapped_families_included_in_candidate": False,
            "removable_cost_proved": False,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--backend-frame", type=int, required=True)
    parser.add_argument("--start-frame", type=int, required=True)
    parser.add_argument("--end-frame", type=int, required=True)
    parser.add_argument("--target", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.log.open(encoding="utf-8", errors="replace") as source:
        result = summarize(source, args.backend_frame, args.start_frame,
                           args.end_frame, set(args.target))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps(result["medians_ms"], indent=2))


if __name__ == "__main__":
    main()
