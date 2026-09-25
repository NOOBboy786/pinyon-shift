import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/analyze-hitches.py"
SPEC = importlib.util.spec_from_file_location("analyze_hitches", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class HitchLoggerTests(unittest.TestCase):
    def test_analyzes_hitches_jsonl_and_detects_root_causes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = pathlib.Path(temp_dir) / "session.hitches.jsonl"
            lines = [
                # Frame 1: Smooth 60 FPS (12ms)
                json.dumps({
                    "schema": 1, "frame": 1, "frame_time_us": 12000, "frame_time_ms": 12.0,
                    "fps": 83.3, "severity": "NONE", "primary_cause": "NORMAL",
                    "draw_calls": 500, "pipeline_cache_misses": 0, "command_buffer_stalls": 0,
                    "texture_cache_hits": 100, "texture_cache_misses": 0
                }),
                # Frame 2: Minor Hitch (22ms) due to Texture Cache Misses
                json.dumps({
                    "schema": 1, "frame": 2, "frame_time_us": 22000, "frame_time_ms": 22.0,
                    "fps": 45.45, "severity": "MINOR", "primary_cause": "TEXTURE_CACHE_UPLOAD",
                    "draw_calls": 800, "pipeline_cache_misses": 0, "command_buffer_stalls": 0,
                    "texture_cache_hits": 50, "texture_cache_misses": 15
                }),
                # Frame 3: Major Hitch (38ms) due to Shader Compilation
                json.dumps({
                    "schema": 1, "frame": 3, "frame_time_us": 38000, "frame_time_ms": 38.0,
                    "fps": 26.3, "severity": "MAJOR", "primary_cause": "SHADER_COMPILATION",
                    "draw_calls": 1200, "pipeline_cache_misses": 4, "command_buffer_stalls": 0,
                    "texture_cache_hits": 120, "texture_cache_misses": 0
                }),
                # Frame 4: Severe Stutter (65ms) due to Command Processor Ring Stall
                json.dumps({
                    "schema": 1, "frame": 4, "frame_time_us": 65000, "frame_time_ms": 65.0,
                    "fps": 15.38, "severity": "SEVERE", "primary_cause": "COMMAND_PROCESSOR_RING_STALL",
                    "draw_calls": 2200, "pipeline_cache_misses": 0, "command_buffer_stalls": 2,
                    "texture_cache_hits": 200, "texture_cache_misses": 0
                }),
                # Frame 5: Critical Stall (120ms) due to UAV Barrier Sync
                json.dumps({
                    "schema": 1, "frame": 5, "frame_time_us": 120000, "frame_time_ms": 120.0,
                    "fps": 8.33, "severity": "CRITICAL_STALL", "primary_cause": "UAV_BARRIER_SYNC",
                    "draw_calls": 1500, "pipeline_cache_misses": 0, "command_buffer_stalls": 0,
                    "memexport_fence_waits": 1, "texture_cache_hits": 100, "texture_cache_misses": 0
                }),
            ]
            log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            result = MODULE.analyze(log_file)
            summary = result["summary"]
            self.assertEqual(summary["total_frames"], 5)
            self.assertEqual(summary["worst_frame_index"], 5)
            self.assertEqual(summary["max_frame_time_ms"], 120.0)

            # Hitch counters
            self.assertEqual(summary["hitches_missed_60fps"]["count"], 4)
            self.assertEqual(summary["hitches_missed_30fps"]["count"], 3)
            self.assertEqual(summary["severe_hitches_50ms"]["count"], 2)
            self.assertEqual(summary["critical_stalls_100ms"]["count"], 1)

            # Root causes
            causes = result["root_causes"]
            self.assertEqual(causes.get("TEXTURE_CACHE_UPLOAD"), 1)
            self.assertEqual(causes.get("SHADER_COMPILATION"), 1)
            self.assertEqual(causes.get("COMMAND_PROCESSOR_RING_STALL"), 1)
            self.assertEqual(causes.get("UAV_BARRIER_SYNC"), 1)

    def test_analyzes_perf_csv_and_infers_causes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_file = pathlib.Path(temp_dir) / "frames.perf.csv"
            header = (
                "frame_time_us,fps,draw_calls,command_buffer_stalls,vertices_processed,"
                "xma_frames_decoded,audio_frame_latency_us,buffer_queue_depth,"
                "functions_dispatched,interrupt_dispatches,active_threads,apc_queue_depth,"
                "critical_region_contentions,texture_cache_hits,texture_cache_misses,"
                "pipeline_cache_hits,pipeline_cache_misses,memexport_draws,memexport_bytes,"
                "memexport_sync_fallbacks,memexport_queue_waits,memexport_fence_waits\n"
            )
            rows = [
                # Frame 0 (init): ignored
                "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0\n",
                # Frame 1 (smooth): 14ms
                "14000,71,600,0,10000,2,1000,1,5000,0,12,0,0,80,0,20,0,0,0,0,0,0\n",
                # Frame 2 (shader spike): 42ms
                "42000,23,1200,0,20000,2,1200,1,6000,0,12,0,0,90,0,15,3,0,0,0,0,0\n",
            ]
            csv_file.write_text(header + "".join(rows), encoding="utf-8")

            result = MODULE.analyze(csv_file)
            summary = result["summary"]
            self.assertEqual(summary["total_frames"], 2)
            self.assertEqual(summary["max_frame_time_ms"], 42.0)
            self.assertEqual(result["root_causes"].get("SHADER_COMPILATION"), 1)

    def test_session_comparison(self):
        base = {
            "source": "base.hitches.jsonl",
            "summary": {
                "total_frames": 100,
                "duration_seconds": 2.0,
                "average_fps": 50.0,
                "median_frame_time_ms": 20.0,
                "p95_frame_time_ms": 32.0,
                "max_frame_time_ms": 50.0,
                "hitches_missed_60fps": {"count": 20, "percent": 20.0},
                "hitches_missed_30fps": {"count": 10, "percent": 10.0},
            }
        }
        cand = {
            "source": "cand.hitches.jsonl",
            "summary": {
                "total_frames": 100,
                "duration_seconds": 1.7,
                "average_fps": 58.8,
                "median_frame_time_ms": 16.5,
                "p95_frame_time_ms": 22.0,
                "max_frame_time_ms": 34.0,
                "hitches_missed_60fps": {"count": 5, "percent": 5.0},
                "hitches_missed_30fps": {"count": 1, "percent": 1.0},
            }
        }
        comp = MODULE.compare_sessions(cand, base)
        self.assertEqual(comp["metrics"]["average_fps"]["delta_pct"], 17.6)
        self.assertEqual(comp["metrics"]["hitch_rate_60fps"]["delta_pct"], -75.0)

    def test_markdown_rendering_contains_expected_sections(self):
        analysis = {
            "source": "test_session.hitches.jsonl",
            "summary": {
                "total_frames": 1000,
                "duration_seconds": 16.6,
                "average_fps": 60.2,
                "median_frame_time_ms": 16.2,
                "p95_frame_time_ms": 18.1,
                "p99_frame_time_ms": 24.5,
                "max_frame_time_ms": 48.0,
                "worst_frame_index": 450,
                "worst_hitch_cause": "SHADER_COMPILATION",
                "hitch_time_ratio_pct": 2.4,
                "hitches_missed_60fps": {"count": 15, "percent": 1.5},
                "hitches_missed_30fps": {"count": 2, "percent": 0.2},
                "severe_hitches_50ms": {"count": 0},
                "critical_stalls_100ms": {"count": 0},
            },
            "latency_distribution": {
                "under_16_6ms": 985,
                "16_6_to_33_3ms": 13,
                "33_3_to_50_0ms": 2,
                "50_0_to_100_0ms": 0,
                "over_100_0ms": 0,
            },
            "root_causes": {"SHADER_COMPILATION": 2, "TEXTURE_CACHE_UPLOAD": 1},
            "worst_hitches": [{
                "frame": 450,
                "frame_time_ms": 48.0,
                "fps": 20.8,
                "primary_cause": "SHADER_COMPILATION",
                "draw_calls": 1200,
                "command_buffer_stalls": 0,
                "pipeline_cache_misses": 2,
                "texture_cache_misses": 0
            }],
            "recommendations": ["Warm up pipeline cache."]
        }
        md = MODULE.render_markdown(analysis)
        self.assertIn("Hitch & Latency Profiling Report", md)
        self.assertIn("Latency Distribution", md)
        self.assertIn("Stutter Root Cause Breakdown", md)
        self.assertIn("SHADER_COMPILATION", md)
        self.assertIn("Top Stutter Spikes", md)
        self.assertIn("Optimization Recommendations", md)

    def test_analyzes_summary_json_without_percentile_key_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary_file = pathlib.Path(temp_dir) / "session.hitch_summary.json"
            summary_data = {
                "schema": 1,
                "session_id": "test_sess",
                "summary": {
                    "total_frames": 500,
                    "duration_seconds": 8.33,
                    "average_fps": 60.0,
                    "max_frame_time_ms": 35.0,
                    "worst_frame_index": 200,
                    "worst_hitch_cause": "UAV_BARRIER_SYNC",
                    "hitch_time_ratio_pct": 1.2,
                    "hitches_missed_60fps": {"count": 4, "percent": 0.8},
                    "hitches_missed_30fps": {"count": 1, "percent": 0.2},
                    "severe_hitches_50ms": {"count": 0},
                    "critical_stalls_100ms": {"count": 0},
                },
                "latency_distribution": {
                    "under_16_6ms": 496,
                    "16_6_to_33_3ms": 3,
                    "33_3_to_50_0ms": 1,
                    "50_0_to_100_0ms": 0,
                    "over_100_0ms": 0,
                },
                "root_causes": {"UAV_BARRIER_SYNC": 1, "TEXTURE_CACHE_UPLOAD": 3}
            }
            summary_file.write_text(json.dumps(summary_data), encoding="utf-8")

            result = MODULE.analyze(summary_file)
            self.assertEqual(result["summary"]["total_frames"], 500)
            self.assertIn("recommendations", result)

            md = MODULE.render_markdown(result)
            self.assertIn("Peak Stutter", md)
            self.assertIn("UAV_BARRIER_SYNC", md)

    def test_smooth_session_with_zero_hitches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = pathlib.Path(temp_dir) / "smooth.hitches.jsonl"
            lines = [
                json.dumps({
                    "schema": 1, "frame": i, "frame_time_us": 12000, "frame_time_ms": 12.0,
                    "fps": 83.3, "severity": "NONE", "primary_cause": "NORMAL",
                    "draw_calls": 500
                })
                for i in range(1, 20)
            ]
            log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            result = MODULE.analyze(log_file)
            self.assertEqual(result["summary"]["hitches_missed_60fps"]["count"], 0)
            self.assertEqual(result["worst_hitches"], [])
            md = MODULE.render_markdown(result)
            self.assertIn("Smooth 60+ FPS", md)

    def test_guest_cpu_stall_classification(self):
        # A 24ms frame with 22ms guest CPU time is a guest CPU stall
        row = {
            "frame_time_us": 24000,
            "guest_cpu_time_us": 22000,
            "pipeline_cache_misses": 0,
            "command_buffer_stalls": 0,
            "texture_cache_misses": 0,
        }
        cause = MODULE.classify_root_cause(row, threshold_us=16667.0)
        self.assertEqual(cause, "GUEST_CPU_STALL")

    def test_custom_threshold_filtering(self):
        # When custom threshold is set to 30ms, a 22ms minor hitch is ignored
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = pathlib.Path(temp_dir) / "threshold_test.hitches.jsonl"
            lines = [
                json.dumps({
                    "schema": 1, "frame": 1, "frame_time_us": 22000, "frame_time_ms": 22.0,
                    "fps": 45.4, "severity": "MINOR", "primary_cause": "TEXTURE_CACHE_UPLOAD",
                    "texture_cache_misses": 10
                }),
                json.dumps({
                    "schema": 1, "frame": 2, "frame_time_us": 40000, "frame_time_ms": 40.0,
                    "fps": 25.0, "severity": "MAJOR", "primary_cause": "SHADER_COMPILATION",
                    "pipeline_cache_misses": 2
                })
            ]
            log_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

            result = MODULE.analyze(log_file, custom_threshold_ms=30.0)
            self.assertEqual(len(result["worst_hitches"]), 1)
            self.assertEqual(result["worst_hitches"][0]["frame"], 2)


if __name__ == "__main__":
    unittest.main()
