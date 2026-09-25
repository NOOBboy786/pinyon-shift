#!/usr/bin/env python3
"""Analyze and summarize Pinyon Shift hitch and latency logs (.hitches.jsonl, .perf.csv, .hitch_summary.json)."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any

SCHEMA = "pinyon-shift.hitch-analysis.v1"

HITCH_THRESHOLDS_US = {
    "minor": 16667,    # 16.67ms (60 FPS threshold)
    "major": 33333,    # 33.33ms (30 FPS threshold)
    "severe": 50000,   # 50.0ms
    "critical": 100000 # 100.0ms
}


class AnalysisError(ValueError):
    """Raised when log data is invalid or cannot be analyzed."""


def classify_root_cause(row: dict[str, Any], threshold_us: float = 16667.0) -> str:
    """Heuristic root cause classifier when parsing raw perf counters or records."""
    if "primary_cause" in row and row["primary_cause"] not in ("UNKNOWN", "", None):
        return str(row["primary_cause"])

    ft_us = float(row.get("frame_time_us", 0))
    if 0 < ft_us < threshold_us:
        return "NORMAL"

    pipe_misses = int(float(row.get("pipeline_cache_misses", 0)))
    cmd_stalls = int(float(row.get("command_buffer_stalls", 0)))
    fence_waits = int(float(row.get("memexport_fence_waits", 0)))
    queue_waits = int(float(row.get("memexport_queue_waits", 0)))
    sync_fallbacks = int(float(row.get("memexport_sync_fallbacks", 0)))
    tex_hits = int(float(row.get("texture_cache_hits", 0)))
    tex_misses = int(float(row.get("texture_cache_misses", 0)))
    tex_total = tex_hits + tex_misses
    contentions = int(float(row.get("critical_region_contentions", 0)))
    audio_latency = int(float(row.get("audio_frame_latency_us", 0)))
    buffer_queue_depth = int(float(row.get("buffer_queue_depth", 0)))
    draw_calls = int(float(row.get("draw_calls", 0)))
    vertices_processed = int(float(row.get("vertices_processed", 0)))
    guest_cpu_us = int(float(row.get("guest_cpu_time_us", 0)))

    if pipe_misses > 0:
        return "SHADER_COMPILATION"
    if cmd_stalls > 0:
        return "COMMAND_PROCESSOR_RING_STALL"
    if fence_waits > 0 or queue_waits > 0 or sync_fallbacks > 0:
        return "UAV_BARRIER_SYNC"
    if tex_misses >= 4 or (tex_total >= 10 and (tex_hits * 100.0 / tex_total) < 85.0):
        return "TEXTURE_CACHE_UPLOAD"
    if contentions > 0:
        return "CPU_LOCK_CONTENTION"
    if guest_cpu_us >= threshold_us and (ft_us <= 0 or guest_cpu_us >= ft_us * 0.6 or guest_cpu_us >= 30000):
        return "GUEST_CPU_STALL"
    if audio_latency >= 15000 or buffer_queue_depth >= 12:
        return "AUDIO_XMA_LATENCY"
    if draw_calls >= 3000 or vertices_processed >= 500000:
        return "HIGH_DRAW_SUBMISSION_VOLUME"
    return "GPU_EXECUTION_OVERLOAD"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct
    low, high = math.floor(pos), math.ceil(pos)
    if low == high:
        return ordered[low]
    weight = pos - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def parse_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_no, line in enumerate(stream, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                records.append(item)
            except json.JSONDecodeError as err:
                raise AnalysisError(f"{path.name}:{line_no}: invalid JSON") from err
    return records


def parse_csv(path: pathlib.Path, threshold_us: float = 16667.0) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for frame_index, row in enumerate(reader, start=1):
            frame_time_us = float(row.get("frame_time_us", 0))
            if frame_time_us <= 0:
                continue
            item = dict(row)
            item["frame"] = frame_index
            item["frame_time_us"] = frame_time_us
            item["frame_time_ms"] = round(frame_time_us / 1000.0, 3)
            item["fps"] = round(1_000_000.0 / frame_time_us, 2)
            item["primary_cause"] = classify_root_cause(item, threshold_us=threshold_us)
            records.append(item)
    return records


def resolve_log_path(path: pathlib.Path) -> pathlib.Path:
    if path.is_file():
        return path
    if path.is_dir():
        for ext in (".hitches.jsonl", ".hitch_summary.json", ".perf.csv"):
            matches = list(path.glob(f"*{ext}"))
            if matches:
                return matches[0]
    # Check if path is a session ID prefix without extension
    parent = path.parent
    name = path.name
    for ext in (".hitches.jsonl", ".hitch_summary.json", ".perf.csv"):
        candidate = parent / f"{name}{ext}"
        if candidate.is_file():
            return candidate
    return path


def analyze(path: pathlib.Path, custom_threshold_ms: float = 16.667) -> dict[str, Any]:
    path = resolve_log_path(path)
    if not path.is_file():
        raise AnalysisError(f"file not found: {path}")

    custom_threshold_us = custom_threshold_ms * 1000.0

    # Check if already a summary JSON
    if path.suffix == ".json" and not path.name.endswith(".jsonl"):
        try:
            with path.open("r", encoding="utf-8") as stream:
                data = json.load(stream)
                if "schema" in data and "summary" in data:
                    if "source" not in data:
                        data["source"] = path.name
                    if "worst_hitches" not in data:
                        data["worst_hitches"] = []
                    if "recommendations" not in data:
                        recs = []
                        causes = data.get("root_causes", {})
                        if causes.get("SHADER_COMPILATION", 0) > 0:
                            recs.append("Warm up pipeline cache / precompile shaders to prevent in-game compilation spikes.")
                        if causes.get("UAV_BARRIER_SYNC", 0) > 0:
                            recs.append("UAV barrier waits detected: confirm adaptive vendor barrier policy is active.")
                        if causes.get("COMMAND_PROCESSOR_RING_STALL", 0) > 0:
                            recs.append("Command buffer stalls detected: ensure draw chunk threshold avoids watchdog limits.")
                        if causes.get("TEXTURE_CACHE_UPLOAD", 0) > 0:
                            recs.append("Texture cache evictions/misses detected: keep anisotropic filtering at 2x and resolution scale at 1x.")
                        if causes.get("GUEST_CPU_STALL", 0) > 0:
                            recs.append("Guest CPU frame simulation spikes detected: check CPU power profile and high-resolution timer.")
                        data["recommendations"] = recs
                    return data
        except Exception:
            pass

    records: list[dict[str, Any]]
    if path.suffix == ".csv":
        records = parse_csv(path, threshold_us=custom_threshold_us)
    else:
        records = parse_jsonl(path)

    if not records:
        raise AnalysisError(f"no records found in {path}")

    custom_threshold_us = custom_threshold_ms * 1000.0
    frame_times = [float(r["frame_time_us"]) for r in records if float(r.get("frame_time_us", 0)) > 0]
    if not frame_times:
        raise AnalysisError("no valid frame times found")

    total_frames = len(frame_times)
    total_time_us = sum(frame_times)
    duration_s = total_time_us / 1_000_000.0
    avg_fps = (total_frames / duration_s) if duration_s > 0 else 0.0

    count_under_16 = 0
    count_16_to_33 = 0
    count_33_to_50 = 0
    count_50_to_100 = 0
    count_over_100 = 0

    hitches = []
    cause_counts: dict[str, int] = {}
    total_hitch_time_us = 0.0

    for r in records:
        ft_us = float(r.get("frame_time_us", 0))
        if ft_us <= 0:
            continue

        if ft_us < HITCH_THRESHOLDS_US["minor"]:
            count_under_16 += 1
        elif ft_us < HITCH_THRESHOLDS_US["major"]:
            count_16_to_33 += 1
        elif ft_us < HITCH_THRESHOLDS_US["severe"]:
            count_33_to_50 += 1
        elif ft_us < HITCH_THRESHOLDS_US["critical"]:
            count_50_to_100 += 1
        else:
            count_over_100 += 1

        if ft_us >= custom_threshold_us:
            total_hitch_time_us += ft_us
            cause = classify_root_cause(r)
            r["primary_cause"] = cause
            cause_counts[cause] = cause_counts.get(cause, 0) + 1
            hitches.append(r)

    p50_us = percentile(frame_times, 0.50)
    p95_us = percentile(frame_times, 0.95)
    p99_us = percentile(frame_times, 0.99)
    max_ft_us = max(frame_times)

    worst_all = sorted(records, key=lambda x: float(x.get("frame_time_us", 0)), reverse=True)
    worst_frame = worst_all[0] if worst_all else {}
    actual_hitches = [r for r in worst_all if float(r.get("frame_time_us", 0)) >= custom_threshold_us]

    total_hitches_16 = count_16_to_33 + count_33_to_50 + count_50_to_100 + count_over_100
    total_hitches_33 = count_33_to_50 + count_50_to_100 + count_over_100

    recommendations = []
    if cause_counts.get("SHADER_COMPILATION", 0) > 0:
        recommendations.append("Warm up pipeline cache / precompile shaders to prevent in-game compilation spikes.")
    if cause_counts.get("UAV_BARRIER_SYNC", 0) > 0:
        recommendations.append("UAV barrier waits detected: confirm adaptive vendor barrier policy is active.")
    if cause_counts.get("COMMAND_PROCESSOR_RING_STALL", 0) > 0:
        recommendations.append("Command buffer stalls detected: ensure draw chunk threshold avoids watchdog limits.")
    if cause_counts.get("TEXTURE_CACHE_UPLOAD", 0) > 0:
        recommendations.append("Texture cache evictions/misses detected: keep anisotropic filtering at 2x and resolution scale at 1x.")
    if cause_counts.get("GUEST_CPU_STALL", 0) > 0:
        recommendations.append("Guest CPU frame simulation spikes detected: check CPU power profile and high-resolution timer.")

    return {
        "schema": SCHEMA,
        "source": path.name,
        "summary": {
            "total_frames": total_frames,
            "duration_seconds": round(duration_s, 3),
            "average_fps": round(avg_fps, 2),
            "median_frame_time_ms": round(p50_us / 1000.0, 3),
            "p95_frame_time_ms": round(p95_us / 1000.0, 3),
            "p99_frame_time_ms": round(p99_us / 1000.0, 3),
            "max_frame_time_ms": round(max_ft_us / 1000.0, 3),
            "worst_frame_index": worst_frame.get("frame", 0),
            "worst_hitch_cause": classify_root_cause(worst_frame, threshold_us=custom_threshold_us) if worst_frame else "NORMAL",
            "hitch_time_ratio_pct": round(total_hitch_time_us * 100.0 / total_time_us, 2) if total_time_us > 0 else 0.0,
            "hitches_missed_60fps": {
                "count": total_hitches_16,
                "percent": round(total_hitches_16 * 100.0 / total_frames, 2),
            },
            "hitches_missed_30fps": {
                "count": total_hitches_33,
                "percent": round(total_hitches_33 * 100.0 / total_frames, 2),
            },
            "severe_hitches_50ms": {
                "count": count_50_to_100 + count_over_100,
            },
            "critical_stalls_100ms": {
                "count": count_over_100,
            },
        },
        "latency_distribution": {
            "under_16_6ms": count_under_16,
            "16_6_to_33_3ms": count_16_to_33,
            "33_3_to_50_0ms": count_33_to_50,
            "50_0_to_100_0ms": count_50_to_100,
            "over_100_0ms": count_over_100,
        },
        "root_causes": cause_counts,
        "worst_hitches": [
            {
                "frame": w.get("frame", 0),
                "frame_time_ms": round(float(w.get("frame_time_us", 0)) / 1000.0, 2),
                "fps": round(float(w.get("fps", 0)), 1),
                "primary_cause": classify_root_cause(w, threshold_us=custom_threshold_us),
                "draw_calls": int(float(w.get("draw_calls", 0))),
                "command_buffer_stalls": int(float(w.get("command_buffer_stalls", 0))),
                "pipeline_cache_misses": int(float(w.get("pipeline_cache_misses", 0))),
                "texture_cache_misses": int(float(w.get("texture_cache_misses", 0))),
            }
            for w in actual_hitches[:5]
        ],
        "recommendations": recommendations,
    }


def compare_sessions(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    c_sum = candidate.get("summary", {})
    b_sum = baseline.get("summary", {})

    def delta(curr: float, prev: float) -> dict[str, Any]:
        pct = round((curr - prev) * 100.0 / prev, 2) if prev != 0 else 0.0
        return {"baseline": prev, "candidate": curr, "delta_pct": pct}

    metrics: dict[str, Any] = {
        "average_fps": delta(float(c_sum.get("average_fps", 0.0)), float(b_sum.get("average_fps", 0.0))),
        "max_frame_time_ms": delta(float(c_sum.get("max_frame_time_ms", 0.0)), float(b_sum.get("max_frame_time_ms", 0.0))),
    }

    if "median_frame_time_ms" in c_sum and "median_frame_time_ms" in b_sum:
        metrics["median_frame_time_ms"] = delta(float(c_sum["median_frame_time_ms"]), float(b_sum["median_frame_time_ms"]))
    if "p95_frame_time_ms" in c_sum and "p95_frame_time_ms" in b_sum:
        metrics["p95_frame_time_ms"] = delta(float(c_sum["p95_frame_time_ms"]), float(b_sum["p95_frame_time_ms"]))

    c_h60 = c_sum.get("hitches_missed_60fps", {}).get("percent", 0.0)
    b_h60 = b_sum.get("hitches_missed_60fps", {}).get("percent", 0.0)
    metrics["hitch_rate_60fps"] = delta(float(c_h60), float(b_h60))

    c_h30 = c_sum.get("hitches_missed_30fps", {}).get("percent", 0.0)
    b_h30 = b_sum.get("hitches_missed_30fps", {}).get("percent", 0.0)
    metrics["hitch_rate_30fps"] = delta(float(c_h30), float(b_h30))

    return {
        "baseline_source": baseline.get("source", "baseline"),
        "candidate_source": candidate.get("source", "candidate"),
        "metrics": metrics,
    }


def render_markdown(analysis: dict[str, Any], comparison: dict[str, Any] | None = None) -> str:
    s = analysis.get("summary", {})
    dist = analysis.get("latency_distribution", {})
    causes = analysis.get("root_causes", {})
    total_frames = s.get("total_frames", 0)

    lines = [
        f"# Hitch & Latency Profiling Report: `{analysis.get('source', 'Session')}`",
        "",
        "## Executive Summary",
        f"- **Sampled Frames:** {total_frames:,}",
        f"- **Duration:** {s.get('duration_seconds', 0.0):.2f} s",
        f"- **Average Framerate:** {s.get('average_fps', 0.0):.1f} FPS",
    ]

    median_val = s.get("median_frame_time_ms")
    p95_val = s.get("p95_frame_time_ms")
    p99_val = s.get("p99_frame_time_ms")
    if median_val is not None and p95_val is not None and p99_val is not None:
        lines.append(f"- **Median Frame Time:** {median_val:.2f} ms (P95: {p95_val:.2f} ms, P99: {p99_val:.2f} ms)")
    elif median_val is not None:
        lines.append(f"- **Median Frame Time:** {median_val:.2f} ms")

    lines.extend([
        f"- **Peak Stutter:** {s.get('max_frame_time_ms', 0.0):.2f} ms (Frame #{s.get('worst_frame_index', 0)}, Cause: `{s.get('worst_hitch_cause', 'NORMAL')}`)",
        f"- **Hitch Time Ratio:** {s.get('hitch_time_ratio_pct', 0.0):.1f}% of playtime spent in stutter",
        "",
        "## Latency Distribution",
        "| Latency Window | Frame Count | Percentage | Target Status |",
        "| :--- | ---: | ---: | :--- |",
    ])

    denom = total_frames if total_frames > 0 else 1
    u16 = dist.get("under_16_6ms", 0)
    w16_33 = dist.get("16_6_to_33_3ms", 0)
    w33_50 = dist.get("33_3_to_50_0ms", 0)
    w50_100 = dist.get("50_0_to_100_0ms", 0)
    o100 = dist.get("over_100_0ms", 0)

    lines.extend([
        f"| **< 16.6 ms** | {u16:,} | {u16 * 100.0 / denom:.1f}% | Smooth 60+ FPS |",
        f"| **16.6 - 33.3 ms** | {w16_33:,} | {w16_33 * 100.0 / denom:.1f}% | Minor Hitch (30-60 FPS) |",
        f"| **33.3 - 50.0 ms** | {w33_50:,} | {w33_50 * 100.0 / denom:.1f}% | Major Hitch (<30 FPS) |",
        f"| **50.0 - 100.0 ms** | {w50_100:,} | {w50_100 * 100.0 / denom:.2f}% | Severe Stutter |",
        f"| **> 100.0 ms** | {o100:,} | {o100 * 100.0 / denom:.2f}% | Critical Stall |",
        "",
    ])

    if causes:
        lines.extend([
            "## Stutter Root Cause Breakdown",
            "| Primary Bottleneck | Hitch Occurrences | Share |",
            "| :--- | ---: | ---: |",
        ])
        total_hitches = sum(causes.values())
        for cause, count in sorted(causes.items(), key=lambda x: x[1], reverse=True):
            pct = count * 100.0 / total_hitches if total_hitches > 0 else 0.0
            lines.append(f"| `{cause}` | {count:,} | {pct:.1f}% |")
        lines.append("")

    if analysis.get("worst_hitches"):
        lines.extend([
            "## Top Stutter Spikes",
            "| Frame | Latency (ms) | FPS | Primary Cause | Draw Calls | Stalls | Shader Misses |",
            "| ---: | ---: | ---: | :--- | ---: | ---: | ---: |",
        ])
        for w in analysis["worst_hitches"]:
            lines.append(
                f"| {w['frame']} | {w['frame_time_ms']:.1f} ms | {w['fps']:.1f} | "
                f"`{w['primary_cause']}` | {w['draw_calls']:,} | {w['command_buffer_stalls']} | {w['pipeline_cache_misses']} |"
            )
        lines.append("")

    if comparison:
        lines.extend([
            "## Baseline Comparison",
            f"Comparing candidate against `{comparison['baseline_source']}`:",
            "",
            "| Metric | Baseline | Candidate | Delta |",
            "| :--- | ---: | ---: | ---: |",
        ])
        for m_name, m_val in comparison["metrics"].items():
            label = m_name.replace("_", " ").title()
            lines.append(f"| {label} | {m_val['baseline']:.2f} | {m_val['candidate']:.2f} | {m_val['delta_pct']:+.2f}% |")
        lines.append("")

    if analysis.get("recommendations"):
        lines.extend(["## Optimization Recommendations"])
        for r in analysis["recommendations"]:
            lines.append(f"- {r}")
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", type=pathlib.Path, help="path to .hitches.jsonl, .perf.csv, or .hitch_summary.json")
    parser.add_argument("--threshold-ms", type=float, default=16.667, help="custom hitch threshold in ms (default: 16.667)")
    parser.add_argument("--baseline", type=pathlib.Path, default=None, help="optional baseline file to compare with")
    parser.add_argument("--format", choices=("markdown", "json", "text"), default="markdown", help="output format")
    parser.add_argument("--output", type=pathlib.Path, default=None, help="write output to file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = analyze(args.log_path, custom_threshold_ms=args.threshold_ms)
        comp = None
        if args.baseline:
            base_result = analyze(args.baseline, custom_threshold_ms=args.threshold_ms)
            comp = compare_sessions(result, base_result)
            result["comparison"] = comp

        if args.format == "json":
            output_text = json.dumps(result, indent=2) + "\n"
        else:
            output_text = render_markdown(result, comp)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output_text, encoding="utf-8")
        else:
            sys.stdout.write(output_text)
        return 0
    except (AnalysisError, OSError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
