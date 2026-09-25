#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <string_view>

namespace pinyon_shift::profiling {

enum class HitchSeverity : uint8_t {
  None,
  Minor,         // >16.6ms (<60 FPS budget)
  Major,         // >33.3ms (<30 FPS budget)
  Severe,        // >50.0ms
  CriticalStall, // >100.0ms
};

enum class HitchRootCause : uint8_t {
  Normal,
  ShaderCompilation,
  CommandProcessorStall,
  UavBarrierSync,
  TextureCacheUpload,
  CpuLockContention,
  GuestCpuStall,
  AudioXmaLatency,
  DrawSubmissionVolume,
  GpuExecutionOverload,
};

const char* HitchSeverityToString(HitchSeverity severity);
const char* HitchRootCauseToString(HitchRootCause cause);

struct FrameRecord {
  int64_t frame_index = 0;
  int64_t frame_time_us = 0;
  double frame_time_ms = 0.0;
  double fps = 0.0;
  HitchSeverity severity = HitchSeverity::None;
  HitchRootCause primary_cause = HitchRootCause::Normal;

  // Latency & execution breakdown
  int64_t guest_cpu_time_us = 0;
  int64_t draw_calls = 0;
  int64_t command_buffer_stalls = 0;
  int64_t vertices_processed = 0;
  int64_t pipeline_cache_hits = 0;
  int64_t pipeline_cache_misses = 0;
  int64_t texture_cache_hits = 0;
  int64_t texture_cache_misses = 0;
  double texture_hit_rate_pct = 100.0;
  int64_t memexport_draws = 0;
  int64_t memexport_bytes = 0;
  int64_t memexport_sync_fallbacks = 0;
  int64_t memexport_queue_waits = 0;
  int64_t memexport_fence_waits = 0;
  int64_t xma_frames_decoded = 0;
  int64_t audio_frame_latency_us = 0;
  int64_t buffer_queue_depth = 0;
  int64_t functions_dispatched = 0;
  int64_t interrupt_dispatches = 0;
  int64_t active_threads = 0;
  int64_t apc_queue_depth = 0;
  int64_t critical_region_contentions = 0;
};

class HitchLogger {
 public:
  static void Initialize(const std::filesystem::path& state_root,
                         const std::string& session_id);
  static void Shutdown();

  static void OnFrameFlipped(int64_t frame_index);
  static void RecordGuestFrameTick();
  static bool IsEnabled();
  static uint64_t GetLastGuestFrameTimeUs();
};

}  // namespace pinyon_shift::profiling
