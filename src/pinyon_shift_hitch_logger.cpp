#include "pinyon_shift_hitch_logger.h"

#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <mutex>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include <fmt/format.h>
#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/perf/counter.h>

#include "pinyon_shift_diagnostics.h"

REXCVAR_DEFINE_BOOL(pinyon_shift_hitch_logger, true, "Pinyon Shift",
                    "Enable dedicated high-fidelity hitch and stutter logger");
REXCVAR_DEFINE_INT32(pinyon_shift_hitch_threshold_ms, 16, "Pinyon Shift",
                     "Frame time threshold in milliseconds to flag as stutter (default: 16)");
REXCVAR_DEFINE_BOOL(pinyon_shift_log_all_frames, false, "Pinyon Shift",
                    "Log all frames to hitches.jsonl regardless of threshold");

namespace pinyon_shift::profiling {

namespace {

constexpr uint32_t kHitchSchemaVersion = 1;

constexpr int64_t kMinorHitchUs = 16667;    // 16.67ms (60 FPS budget)
constexpr int64_t kMajorHitchUs = 33333;    // 33.33ms (30 FPS budget)
constexpr int64_t kSevereHitchUs = 50000;   // 50.0ms (severe stutter)
constexpr int64_t kCriticalStallUs = 100000; // 100.0ms (critical stall / freeze)

std::filesystem::path g_hitches_path;
std::filesystem::path g_summary_path;
std::string g_session_id;

std::mutex g_logger_mutex;
std::FILE* g_hitches_file = nullptr;
bool g_initialized = false;

std::atomic<uint64_t> g_last_guest_cpu_time_us{0};
std::atomic<uint64_t> g_last_guest_tick_us{0};
std::atomic<uint64_t> g_guest_frame_accum_us{0};

constexpr size_t kHistogramBuckets = 300; // 0ms to 299ms (1ms buckets), 300+ in bucket 299

// Cumulative statistics
struct SessionStats {
  int64_t total_frames = 0;
  int64_t total_frame_time_us = 0;
  int64_t max_frame_time_us = 0;
  int64_t max_frame_index = 0;
  HitchRootCause worst_hitch_cause = HitchRootCause::Normal;

  int64_t count_under_16ms = 0;
  int64_t count_16_to_33ms = 0;
  int64_t count_33_to_50ms = 0;
  int64_t count_50_to_100ms = 0;
  int64_t count_over_100ms = 0;

  int64_t total_hitch_time_us = 0; // time in frames >= threshold

  uint32_t frame_time_buckets[kHistogramBuckets] = {0};

  std::unordered_map<std::string, int64_t> cause_counts;
} g_stats;

}  // anonymous namespace

const char* HitchSeverityToString(HitchSeverity severity) {
  switch (severity) {
    case HitchSeverity::None: return "NONE";
    case HitchSeverity::Minor: return "MINOR";
    case HitchSeverity::Major: return "MAJOR";
    case HitchSeverity::Severe: return "SEVERE";
    case HitchSeverity::CriticalStall: return "CRITICAL_STALL";
    default: return "UNKNOWN";
  }
}

const char* HitchRootCauseToString(HitchRootCause cause) {
  switch (cause) {
    case HitchRootCause::Normal: return "NORMAL";
    case HitchRootCause::ShaderCompilation: return "SHADER_COMPILATION";
    case HitchRootCause::CommandProcessorStall: return "COMMAND_PROCESSOR_RING_STALL";
    case HitchRootCause::UavBarrierSync: return "UAV_BARRIER_SYNC";
    case HitchRootCause::TextureCacheUpload: return "TEXTURE_CACHE_UPLOAD";
    case HitchRootCause::CpuLockContention: return "CPU_LOCK_CONTENTION";
    case HitchRootCause::GuestCpuStall: return "GUEST_CPU_STALL";
    case HitchRootCause::AudioXmaLatency: return "AUDIO_XMA_LATENCY";
    case HitchRootCause::DrawSubmissionVolume: return "HIGH_DRAW_SUBMISSION_VOLUME";
    case HitchRootCause::GpuExecutionOverload: return "GPU_EXECUTION_OVERLOAD";
    default: return "UNKNOWN";
  }
}

void HitchLogger::RecordGuestFrameTick() {
  const uint64_t now_us = static_cast<uint64_t>(
      std::chrono::duration_cast<std::chrono::microseconds>(
          std::chrono::steady_clock::now().time_since_epoch()).count());
  uint64_t prev = g_last_guest_tick_us.exchange(now_us, std::memory_order_acq_rel);
  if (prev != 0 && now_us > prev) {
    const uint64_t delta_us = now_us - prev;
    g_last_guest_cpu_time_us.store(delta_us, std::memory_order_release);
    g_guest_frame_accum_us.fetch_add(delta_us, std::memory_order_relaxed);
  }
}

uint64_t HitchLogger::GetLastGuestFrameTimeUs() {
  return g_last_guest_cpu_time_us.load(std::memory_order_relaxed);
}

bool HitchLogger::IsEnabled() {
  return REXCVAR_GET(pinyon_shift_hitch_logger);
}

void HitchLogger::Initialize(const std::filesystem::path& state_root,
                             const std::string& session_id) {
  std::lock_guard lock(g_logger_mutex);
  if (g_initialized) {
    return;
  }

  g_session_id = session_id;
  const auto logs_dir = state_root / "logs";
  std::error_code ec;
  std::filesystem::create_directories(logs_dir, ec);

  g_hitches_path = logs_dir / (session_id + ".hitches.jsonl");
  g_summary_path = logs_dir / (session_id + ".hitch_summary.json");

#if defined(_WIN32)
  _wfopen_s(&g_hitches_file, g_hitches_path.c_str(), L"a");
#else
  g_hitches_file = std::fopen(g_hitches_path.string().c_str(), "a");
#endif

  g_stats = {};
  g_initialized = true;

  rex::perf::SetFrameCallback(&HitchLogger::OnFrameFlipped);

  pinyon_shift::diagnostics::RecordEvent(
      "profiler.hitch_logger.ready",
      {{"schema", std::to_string(kHitchSchemaVersion)},
       {"log_path", g_hitches_path.string()},
       {"threshold_ms", std::to_string(REXCVAR_GET(pinyon_shift_hitch_threshold_ms))},
       {"log_all_frames", REXCVAR_GET(pinyon_shift_log_all_frames) ? "1" : "0"}});

  REXLOG_INFO("Hitch & Latency Logger active: recording to {}", g_hitches_path.string());
}

void HitchLogger::OnFrameFlipped(int64_t frame_index) {
  if (!IsEnabled() || !g_initialized) {
    return;
  }

  const int64_t frame_time_us =
      rex::perf::GetSnapshotCounter(rex::perf::CounterId::kFrameTimeUs);
  if (frame_time_us <= 0) {
    // Initialization row or unmeasured frame; ignore
    return;
  }

  FrameRecord rec;
  rec.frame_index = frame_index;
  rec.frame_time_us = frame_time_us;
  rec.frame_time_ms = static_cast<double>(frame_time_us) / 1000.0;
  rec.fps = frame_time_us > 0 ? (1000000.0 / static_cast<double>(frame_time_us)) : 0.0;

  // Measure guest CPU time for this presentation frame
  uint64_t guest_accum = g_guest_frame_accum_us.exchange(0, std::memory_order_acq_rel);
  if (guest_accum > 0) {
    rec.guest_cpu_time_us = static_cast<int64_t>(guest_accum);
  } else {
    // If no tick finished this frame, check how long since the last tick began (active guest stall)
    const uint64_t now_us = static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now().time_since_epoch()).count());
    const uint64_t last_tick = g_last_guest_tick_us.load(std::memory_order_acquire);
    if (last_tick != 0 && now_us > last_tick) {
      rec.guest_cpu_time_us = static_cast<int64_t>(now_us - last_tick);
    } else {
      rec.guest_cpu_time_us = static_cast<int64_t>(g_last_guest_cpu_time_us.load(std::memory_order_relaxed));
    }
  }

  // Query performance counters
  rec.draw_calls = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kDrawCalls);
  rec.command_buffer_stalls = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kCommandBufferStalls);
  rec.vertices_processed = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kVerticesProcessed);
  rec.pipeline_cache_hits = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kPipelineCacheHits);
  rec.pipeline_cache_misses = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kPipelineCacheMisses);
  rec.texture_cache_hits = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kTextureCacheHits);
  rec.texture_cache_misses = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kTextureCacheMisses);
  const int64_t tex_total = rec.texture_cache_hits + rec.texture_cache_misses;
  rec.texture_hit_rate_pct =
      tex_total > 0 ? (static_cast<double>(rec.texture_cache_hits) * 100.0 / tex_total) : 100.0;

  rec.memexport_draws = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kMemexportDraws);
  rec.memexport_bytes = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kMemexportBytes);
  rec.memexport_sync_fallbacks = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kMemexportSyncFallbacks);
  rec.memexport_queue_waits = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kMemexportQueueWaits);
  rec.memexport_fence_waits = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kMemexportFenceWaits);

  rec.xma_frames_decoded = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kXmaFramesDecoded);
  rec.audio_frame_latency_us = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kAudioFrameLatencyUs);
  rec.buffer_queue_depth = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kBufferQueueDepth);

  rec.functions_dispatched = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kFunctionsDispatched);
  rec.interrupt_dispatches = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kInterruptDispatches);
  rec.active_threads = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kActiveThreads);
  rec.apc_queue_depth = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kApcQueueDepth);
  rec.critical_region_contentions = rex::perf::GetSnapshotCounter(rex::perf::CounterId::kCriticalRegionContentions);

  // Evaluate user threshold
  const int32_t user_threshold_ms = REXCVAR_GET(pinyon_shift_hitch_threshold_ms);
  const int64_t active_threshold_us =
      user_threshold_ms > 0 ? (static_cast<int64_t>(user_threshold_ms) * 1000) : kMinorHitchUs;

  // Determine Severity strictly gated by active threshold
  if (frame_time_us < active_threshold_us) {
    rec.severity = HitchSeverity::None;
  } else if (frame_time_us >= kCriticalStallUs) {
    rec.severity = HitchSeverity::CriticalStall;
  } else if (frame_time_us >= kSevereHitchUs) {
    rec.severity = HitchSeverity::Severe;
  } else if (frame_time_us >= kMajorHitchUs) {
    rec.severity = HitchSeverity::Major;
  } else {
    rec.severity = HitchSeverity::Minor;
  }

  // Determine Root Cause Heuristic
  if (rec.severity != HitchSeverity::None) {
    if (rec.pipeline_cache_misses > 0) {
      rec.primary_cause = HitchRootCause::ShaderCompilation;
    } else if (rec.command_buffer_stalls > 0) {
      rec.primary_cause = HitchRootCause::CommandProcessorStall;
    } else if (rec.memexport_fence_waits > 0 || rec.memexport_queue_waits > 0 ||
               rec.memexport_sync_fallbacks > 0) {
      rec.primary_cause = HitchRootCause::UavBarrierSync;
    } else if (rec.texture_cache_misses >= 4 || (tex_total >= 10 && rec.texture_hit_rate_pct < 85.0)) {
      rec.primary_cause = HitchRootCause::TextureCacheUpload;
    } else if (rec.critical_region_contentions > 0) {
      rec.primary_cause = HitchRootCause::CpuLockContention;
    } else if (rec.guest_cpu_time_us >= active_threshold_us &&
               (rec.guest_cpu_time_us >= static_cast<int64_t>(rec.frame_time_us * 0.6) ||
                rec.guest_cpu_time_us >= 30000)) {
      rec.primary_cause = HitchRootCause::GuestCpuStall;
    } else if (rec.audio_frame_latency_us >= 15000 || rec.buffer_queue_depth >= 12) {
      rec.primary_cause = HitchRootCause::AudioXmaLatency;
    } else if (rec.draw_calls >= 3000 || rec.vertices_processed >= 500000) {
      rec.primary_cause = HitchRootCause::DrawSubmissionVolume;
    } else {
      rec.primary_cause = HitchRootCause::GpuExecutionOverload;
    }
  }

  const bool should_log =
      (rec.severity != HitchSeverity::None) || REXCVAR_GET(pinyon_shift_log_all_frames);

  // Update statistics and output
  std::lock_guard lock(g_logger_mutex);
  g_stats.total_frames++;
  g_stats.total_frame_time_us += frame_time_us;

  const size_t bucket = std::min<size_t>(
      static_cast<size_t>(frame_time_us / 1000), kHistogramBuckets - 1);
  g_stats.frame_time_buckets[bucket]++;

  if (frame_time_us < kMinorHitchUs) {
    g_stats.count_under_16ms++;
  } else if (frame_time_us < kMajorHitchUs) {
    g_stats.count_16_to_33ms++;
  } else if (frame_time_us < kSevereHitchUs) {
    g_stats.count_33_to_50ms++;
  } else if (frame_time_us < kCriticalStallUs) {
    g_stats.count_50_to_100ms++;
  } else {
    g_stats.count_over_100ms++;
  }

  if (rec.severity != HitchSeverity::None) {
    g_stats.total_hitch_time_us += frame_time_us;
    g_stats.cause_counts[HitchRootCauseToString(rec.primary_cause)]++;
  }

  if (frame_time_us > g_stats.max_frame_time_us) {
    g_stats.max_frame_time_us = frame_time_us;
    g_stats.max_frame_index = frame_index;
    g_stats.worst_hitch_cause = rec.primary_cause;
  }

  if (should_log && g_hitches_file) {
    const std::string line = fmt::format(
        "{{\"schema\":{},\"frame\":{},\"frame_time_us\":{},\"frame_time_ms\":{:.2f},"
        "\"fps\":{:.2f},\"severity\":\"{}\",\"primary_cause\":\"{}\","
        "\"guest_cpu_time_us\":{},\"draw_calls\":{},\"command_buffer_stalls\":{},"
        "\"vertices_processed\":{},\"pipeline_cache_hits\":{},\"pipeline_cache_misses\":{},"
        "\"texture_cache_hits\":{},\"texture_cache_misses\":{},\"texture_hit_rate_pct\":{:.2f},"
        "\"memexport_draws\":{},\"memexport_bytes\":{},\"memexport_sync_fallbacks\":{},"
        "\"memexport_queue_waits\":{},\"memexport_fence_waits\":{},\"xma_frames_decoded\":{},"
        "\"audio_frame_latency_us\":{},\"buffer_queue_depth\":{},\"functions_dispatched\":{},"
        "\"interrupt_dispatches\":{},\"active_threads\":{},\"apc_queue_depth\":{},"
        "\"critical_region_contentions\":{}}}\n",
        kHitchSchemaVersion, rec.frame_index, rec.frame_time_us, rec.frame_time_ms,
        rec.fps, HitchSeverityToString(rec.severity), HitchRootCauseToString(rec.primary_cause),
        rec.guest_cpu_time_us, rec.draw_calls, rec.command_buffer_stalls,
        rec.vertices_processed, rec.pipeline_cache_hits, rec.pipeline_cache_misses,
        rec.texture_cache_hits, rec.texture_cache_misses, rec.texture_hit_rate_pct,
        rec.memexport_draws, rec.memexport_bytes, rec.memexport_sync_fallbacks,
        rec.memexport_queue_waits, rec.memexport_fence_waits, rec.xma_frames_decoded,
        rec.audio_frame_latency_us, rec.buffer_queue_depth, rec.functions_dispatched,
        rec.interrupt_dispatches, rec.active_threads, rec.apc_queue_depth,
        rec.critical_region_contentions);

    std::fputs(line.c_str(), g_hitches_file);
    if (rec.severity != HitchSeverity::None) {
      std::fflush(g_hitches_file);
    }
  }

  // Major and severe hitches get logged to master diagnostics
  if (rec.severity >= HitchSeverity::Major) {
    pinyon_shift::diagnostics::RecordEvent(
        "frame.hitch",
        {{"frame", std::to_string(rec.frame_index)},
         {"frame_time_ms", fmt::format("{:.2f}", rec.frame_time_ms)},
         {"fps", fmt::format("{:.1f}", rec.fps)},
         {"severity", HitchSeverityToString(rec.severity)},
         {"primary_cause", HitchRootCauseToString(rec.primary_cause)},
         {"draw_calls", std::to_string(rec.draw_calls)},
         {"command_buffer_stalls", std::to_string(rec.command_buffer_stalls)},
         {"pipeline_cache_misses", std::to_string(rec.pipeline_cache_misses)},
         {"texture_cache_misses", std::to_string(rec.texture_cache_misses)},
         {"memexport_fence_waits", std::to_string(rec.memexport_fence_waits)},
         {"audio_latency_us", std::to_string(rec.audio_frame_latency_us)}});

    if (rec.severity >= HitchSeverity::Severe) {
      REXLOG_WARN(
          "STUTTER [Frame {}] {:.1f}ms (Severity: {}, Bottleneck: {}) - Draws: {}, Stalls: {}, ShaderMisses: {}, TexMisses: {}",
          rec.frame_index, rec.frame_time_ms, HitchSeverityToString(rec.severity),
          HitchRootCauseToString(rec.primary_cause), rec.draw_calls,
          rec.command_buffer_stalls, rec.pipeline_cache_misses, rec.texture_cache_misses);
    }
  }
}

void HitchLogger::Shutdown() {
  std::lock_guard lock(g_logger_mutex);
  if (!g_initialized) {
    return;
  }
  g_initialized = false;
  rex::perf::SetFrameCallback(nullptr);

  if (g_hitches_file) {
    std::fflush(g_hitches_file);
    std::fclose(g_hitches_file);
    g_hitches_file = nullptr;
  }

  if (g_stats.total_frames == 0) {
    return;
  }

  const double duration_seconds = static_cast<double>(g_stats.total_frame_time_us) / 1000000.0;
  const double avg_fps = duration_seconds > 0 ? (static_cast<double>(g_stats.total_frames) / duration_seconds) : 0.0;
  const double max_frame_ms = static_cast<double>(g_stats.max_frame_time_us) / 1000.0;
  const int64_t total_hitches_16ms =
      g_stats.count_16_to_33ms + g_stats.count_33_to_50ms + g_stats.count_50_to_100ms + g_stats.count_over_100ms;
  const int64_t total_hitches_33ms =
      g_stats.count_33_to_50ms + g_stats.count_50_to_100ms + g_stats.count_over_100ms;
  const int64_t total_hitches_50ms = g_stats.count_50_to_100ms + g_stats.count_over_100ms;

  const double hitch_16_pct = static_cast<double>(total_hitches_16ms) * 100.0 / g_stats.total_frames;
  const double hitch_33_pct = static_cast<double>(total_hitches_33ms) * 100.0 / g_stats.total_frames;
  const double hitch_time_pct = duration_seconds > 0 ?
      (static_cast<double>(g_stats.total_hitch_time_us) * 100.0 / g_stats.total_frame_time_us) : 0.0;

  // Calculate percentiles from frame time histogram
  double p50_ms = 0.0;
  double p95_ms = 0.0;
  double p99_ms = 0.0;
  if (g_stats.total_frames > 0) {
    const int64_t target_50 = (g_stats.total_frames * 50) / 100;
    const int64_t target_95 = (g_stats.total_frames * 95) / 100;
    const int64_t target_99 = (g_stats.total_frames * 99) / 100;
    int64_t accum = 0;
    for (size_t i = 0; i < kHistogramBuckets; ++i) {
      accum += g_stats.frame_time_buckets[i];
      if (p50_ms == 0.0 && accum >= target_50) {
        p50_ms = static_cast<double>(i) + 0.5;
      }
      if (p95_ms == 0.0 && accum >= target_95) {
        p95_ms = static_cast<double>(i) + 0.5;
      }
      if (p99_ms == 0.0 && accum >= target_99) {
        p99_ms = static_cast<double>(i) + 0.5;
      }
    }
  }

  // Build JSON summary
  std::ostringstream json;
  json << "{\n";
  json << "  \"schema\": " << kHitchSchemaVersion << ",\n";
  json << "  \"session_id\": \"" << g_session_id << "\",\n";
  json << "  \"summary\": {\n";
  json << "    \"total_frames\": " << g_stats.total_frames << ",\n";
  json << "    \"duration_seconds\": " << std::fixed << std::setprecision(3) << duration_seconds << ",\n";
  json << "    \"average_fps\": " << std::fixed << std::setprecision(2) << avg_fps << ",\n";
  json << "    \"median_frame_time_ms\": " << std::fixed << std::setprecision(2) << p50_ms << ",\n";
  json << "    \"p95_frame_time_ms\": " << std::fixed << std::setprecision(2) << p95_ms << ",\n";
  json << "    \"p99_frame_time_ms\": " << std::fixed << std::setprecision(2) << p99_ms << ",\n";
  json << "    \"max_frame_time_ms\": " << std::fixed << std::setprecision(2) << max_frame_ms << ",\n";
  json << "    \"worst_frame_index\": " << g_stats.max_frame_index << ",\n";
  json << "    \"worst_hitch_cause\": \"" << HitchRootCauseToString(g_stats.worst_hitch_cause) << "\",\n";
  json << "    \"hitch_time_ratio_pct\": " << std::fixed << std::setprecision(2) << hitch_time_pct << ",\n";
  json << "    \"hitches_missed_60fps\": {\"count\": " << total_hitches_16ms << ", \"percent\": " << std::fixed << std::setprecision(2) << hitch_16_pct << "},\n";
  json << "    \"hitches_missed_30fps\": {\"count\": " << total_hitches_33ms << ", \"percent\": " << std::fixed << std::setprecision(2) << hitch_33_pct << "},\n";
  json << "    \"severe_hitches_50ms\": {\"count\": " << total_hitches_50ms << "},\n";
  json << "    \"critical_stalls_100ms\": {\"count\": " << g_stats.count_over_100ms << "}\n";
  json << "  },\n";
  json << "  \"latency_distribution\": {\n";
  json << "    \"under_16_6ms\": " << g_stats.count_under_16ms << ",\n";
  json << "    \"16_6_to_33_3ms\": " << g_stats.count_16_to_33ms << ",\n";
  json << "    \"33_3_to_50_0ms\": " << g_stats.count_33_to_50ms << ",\n";
  json << "    \"50_0_to_100_0ms\": " << g_stats.count_50_to_100ms << ",\n";
  json << "    \"over_100_0ms\": " << g_stats.count_over_100ms << "\n";
  json << "  },\n";
  json << "  \"root_causes\": {\n";
  size_t cause_index = 0;
  for (const auto& [cause_name, count] : g_stats.cause_counts) {
    if (cause_index++ > 0) json << ",\n";
    json << "    \"" << cause_name << "\": " << count;
  }
  json << "\n  }\n";
  json << "}\n";

  std::ofstream summary_out(g_summary_path);
  if (summary_out) {
    summary_out << json.str();
    summary_out.close();
  }

  pinyon_shift::diagnostics::RecordEvent(
      "hitch_logger.summary",
      {{"total_frames", std::to_string(g_stats.total_frames)},
       {"duration_s", fmt::format("{:.2f}", duration_seconds)},
       {"average_fps", fmt::format("{:.1f}", avg_fps)},
       {"median_frame_time_ms", fmt::format("{:.2f}", p50_ms)},
       {"p95_frame_time_ms", fmt::format("{:.2f}", p95_ms)},
       {"p99_frame_time_ms", fmt::format("{:.2f}", p99_ms)},
       {"max_frame_time_ms", fmt::format("{:.2f}", max_frame_ms)},
       {"worst_frame", std::to_string(g_stats.max_frame_index)},
       {"worst_cause", HitchRootCauseToString(g_stats.worst_hitch_cause)},
       {"hitches_16ms", std::to_string(total_hitches_16ms)},
       {"hitches_33ms", std::to_string(total_hitches_33ms)},
       {"stalls_100ms", std::to_string(g_stats.count_over_100ms)}});

  // Human-readable console banner
  REXLOG_INFO("============================================================");
  REXLOG_INFO("          PINYON SHIFT HITCH & LATENCY REPORT               ");
  REXLOG_INFO("============================================================");
  REXLOG_INFO("Session: {}", g_session_id);
  REXLOG_INFO("Frames: {} | Duration: {:.2f}s | Avg FPS: {:.1f}",
              g_stats.total_frames, duration_seconds, avg_fps);
  REXLOG_INFO("Median Frame Time: {:.1f}ms | P95: {:.1f}ms | P99: {:.1f}ms",
              p50_ms, p95_ms, p99_ms);
  REXLOG_INFO("Peak Stutter: {:.1f}ms (Frame #{}, Primary: {})",
              max_frame_ms, g_stats.max_frame_index,
              HitchRootCauseToString(g_stats.worst_hitch_cause));
  REXLOG_INFO("Latency Breakdown:");
  REXLOG_INFO("  Smooth (<16.6ms / 60+ FPS):  {:6d} ({:5.1f}%)",
              g_stats.count_under_16ms,
              static_cast<double>(g_stats.count_under_16ms) * 100.0 / g_stats.total_frames);
  REXLOG_INFO("  Minor Hitch (16.6 - 33.3ms): {:6d} ({:5.1f}%)",
              g_stats.count_16_to_33ms,
              static_cast<double>(g_stats.count_16_to_33ms) * 100.0 / g_stats.total_frames);
  REXLOG_INFO("  Major Hitch (33.3 - 50.0ms): {:6d} ({:5.1f}%)",
              g_stats.count_33_to_50ms,
              static_cast<double>(g_stats.count_33_to_50ms) * 100.0 / g_stats.total_frames);
  REXLOG_INFO("  Severe Hitch (50 - 100ms):   {:6d} ({:5.1f}%)",
              g_stats.count_50_to_100ms,
              static_cast<double>(g_stats.count_50_to_100ms) * 100.0 / g_stats.total_frames);
  REXLOG_INFO("  Critical Stall (>100ms):     {:6d} ({:5.1f}%)",
              g_stats.count_over_100ms,
              static_cast<double>(g_stats.count_over_100ms) * 100.0 / g_stats.total_frames);
  if (!g_stats.cause_counts.empty()) {
    REXLOG_INFO("Stutter Root Causes:");
    for (const auto& [cause_name, count] : g_stats.cause_counts) {
      const double pct = total_hitches_16ms > 0 ? (static_cast<double>(count) * 100.0 / total_hitches_16ms) : 0.0;
      REXLOG_INFO("  - {:30s}: {:4d} ({:4.1f}% of hitches)",
                  cause_name, count, pct);
    }
  }
  REXLOG_INFO("Summary saved to: {}", g_summary_path.string());
  REXLOG_INFO("============================================================");
}

}  // namespace pinyon_shift::profiling
