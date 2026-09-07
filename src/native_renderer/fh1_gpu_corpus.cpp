#include "native_renderer/fh1_gpu_corpus.h"

#include <atomic>
#include <array>
#include <filesystem>
#include <fstream>
#include <map>
#include <mutex>

#include <fmt/format.h>
#include <rex/cvar.h>

#include "native_renderer/fh1_pass_tracker.h"
#include "pinyon_shift_diagnostics.h"

REXCVAR_DEFINE_BOOL(pinyon_shift_fh1_gpu_corpus, false, "Pinyon Shift",
                    "Record the local FH1 V4 GPU execution corpus")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

namespace pinyon_shift::native_renderer {
namespace {

constexpr size_t kMaximumCorpusKeys = 65536;

struct CorpusEntry {
  rex::system::GraphicsFh1ExecutionKey key;
  uint64_t vertex_shader = 0;
  uint64_t pixel_shader = 0;
  uint64_t count = 0;
  uint64_t first_frame = 0;
  uint64_t last_frame = 0;
  uint32_t index_count = 0;
  uint32_t index_buffer_guest_base = 0;
  uint32_t index_buffer_length = 0;
  rex::system::GraphicsCopyObservation copy;
  bool has_copy = false;
};

struct PassEntry {
  Fh1PassSummary summary;
  uint64_t occurrences = 0;
  uint64_t draw_executions = 0;
  uint64_t first_frame = 0;
  uint64_t last_frame = 0;
};

std::atomic<bool> g_enabled{false};
std::mutex g_mutex;
std::map<uint64_t, CorpusEntry> g_entries;
std::map<uint64_t, PassEntry> g_passes;
Fh1PassTracker g_pass_tracker;
uint64_t g_overflow = 0;
uint64_t g_collisions = 0;
uint64_t g_pass_collisions = 0;
std::array<std::atomic<uint64_t>, 2> g_mode_counts{};
std::array<std::atomic<uint64_t>, 5> g_fallback_counts{};
std::atomic<uint64_t> g_runtime_shader_translations{0};
std::atomic<uint64_t> g_runtime_sync_pipeline_creations{0};

CorpusEntry* RecordKeyLocked(const rex::system::GraphicsFh1ExecutionKey& key,
                             uint64_t frame, uint64_t vertex_shader,
                             uint64_t pixel_shader, uint32_t index_count = 0,
                             uint32_t index_buffer_guest_base = 0,
                             uint32_t index_buffer_length = 0) {
  auto found = g_entries.find(key.identity);
  if (found != g_entries.end()) {
    if (found->second.key != key) {
      ++g_collisions;
      return nullptr;
    }
    ++found->second.count;
    found->second.last_frame = frame;
    return &found->second;
  }
  if (g_entries.size() == kMaximumCorpusKeys) {
    ++g_overflow;
    return nullptr;
  }
  return &g_entries
              .emplace(key.identity,
                       CorpusEntry{key, vertex_shader, pixel_shader, 1, frame,
                                   frame, index_count,
                                   index_buffer_guest_base,
                                   index_buffer_length})
              .first->second;
}

void RecordPassLocked(const Fh1PassSummary& summary) {
  auto [found, inserted] = g_passes.try_emplace(
      summary.signature,
      PassEntry{summary, 1, summary.draw_count, summary.frame,
                summary.frame});
  if (inserted) {
    return;
  }
  if (found->second.summary.attachment_state != summary.attachment_state ||
      found->second.summary.first_draw_family != summary.first_draw_family ||
      found->second.summary.first_draw_identity != summary.first_draw_identity ||
      found->second.summary.terminal_copy_state !=
          summary.terminal_copy_state ||
      found->second.summary.draw_count != summary.draw_count) {
    ++g_pass_collisions;
    return;
  }
  ++found->second.occurrences;
  found->second.draw_executions += summary.draw_count;
  found->second.summary.prepare_cpu_time_ns += summary.prepare_cpu_time_ns;
  found->second.last_frame = summary.frame;
  found->second.summary.hazard_flags |= summary.hazard_flags;
}

}  // namespace

bool ResetFh1GpuCorpus() {
  std::lock_guard lock(g_mutex);
  g_entries.clear();
  g_passes.clear();
  g_pass_tracker = {};
  g_overflow = 0;
  g_collisions = 0;
  g_pass_collisions = 0;
  for (auto& count : g_mode_counts) {
    count.store(0, std::memory_order_relaxed);
  }
  for (auto& count : g_fallback_counts) {
    count.store(0, std::memory_order_relaxed);
  }
  g_runtime_shader_translations.store(0, std::memory_order_relaxed);
  g_runtime_sync_pipeline_creations.store(0, std::memory_order_relaxed);
  const bool enabled = REXCVAR_GET(pinyon_shift_fh1_gpu_corpus);
  g_enabled.store(enabled, std::memory_order_release);
  return enabled;
}

void RecordFh1GpuExecution(
    const rex::system::GraphicsPreparedDrawObservation& observation) {
  const size_t mode = static_cast<size_t>(observation.fh1_execution_mode);
  const size_t fallback = static_cast<size_t>(observation.fh1_fallback_reason);
  if (mode < g_mode_counts.size()) {
    g_mode_counts[mode].fetch_add(1, std::memory_order_relaxed);
  }
  if (fallback < g_fallback_counts.size()) {
    g_fallback_counts[fallback].fetch_add(1, std::memory_order_relaxed);
  }
  g_runtime_shader_translations.store(
      observation.fh1_runtime_shader_translations,
      std::memory_order_relaxed);
  g_runtime_sync_pipeline_creations.store(
      observation.fh1_runtime_sync_pipeline_creations,
      std::memory_order_relaxed);
  const auto& key = observation.fh1_execution_key;
  if (!g_enabled.load(std::memory_order_acquire) ||
      key.version != rex::system::GraphicsFh1ExecutionKey::kVersion ||
      !key.identity || key.identity != key.ComputeIdentity()) {
    return;
  }
  std::lock_guard lock(g_mutex);
  if (const auto pass =
          g_pass_tracker.ObserveDraw(key, observation.frame_sequence,
                                     observation.fh1_prepare_cpu_time_ns)) {
    RecordPassLocked(*pass);
  }
  RecordKeyLocked(key, observation.frame_sequence,
                  observation.vertex_shader_hash,
                  observation.pixel_shader_hash, observation.index_count,
                  observation.index_buffer_guest_base,
                  observation.index_buffer_length);
}

void RecordFh1GpuCopy(
    const rex::system::GraphicsCopyObservation& observation) {
  const auto& key = observation.fh1_execution_key;
  if (!g_enabled.load(std::memory_order_acquire) ||
      key.version != rex::system::GraphicsFh1ExecutionKey::kVersion ||
      !key.identity || key.identity != key.ComputeIdentity()) {
    return;
  }
  std::lock_guard lock(g_mutex);
  if (const auto pass =
          g_pass_tracker.ObserveCopy(key, observation.frame_sequence)) {
    RecordPassLocked(*pass);
  }
  if (auto* entry =
          RecordKeyLocked(key, observation.frame_sequence, 0, 0)) {
    entry->copy = observation;
    entry->has_copy = true;
  }
}

void RecordFh1GpuExecution(
    const rex::system::GraphicsFh1ExecutionKey& key, uint64_t frame,
    uint64_t vertex_shader, uint64_t pixel_shader) {
  if (!g_enabled.load(std::memory_order_acquire) ||
      key.version != rex::system::GraphicsFh1ExecutionKey::kVersion ||
      !key.identity || key.identity != key.ComputeIdentity()) {
    return;
  }
  std::lock_guard lock(g_mutex);
  RecordKeyLocked(key, frame, vertex_shader, pixel_shader);
}

void FlushFh1GpuCorpus() {
  if (!g_enabled.exchange(false, std::memory_order_acq_rel)) {
    return;
  }
  diagnostics::RecordEvent(
      "native_renderer.v4.execution.summary",
      {{"compatibility",
        fmt::format("{}", g_mode_counts[0].load(std::memory_order_relaxed))},
       {"covered_in_place",
        fmt::format("{}", g_mode_counts[1].load(std::memory_order_relaxed))},
       {"manifest_unavailable",
        fmt::format("{}", g_fallback_counts[1].load(std::memory_order_relaxed))},
       {"key_not_captured",
        fmt::format("{}", g_fallback_counts[2].load(std::memory_order_relaxed))},
       {"hazardous_draw",
        fmt::format("{}", g_fallback_counts[3].load(std::memory_order_relaxed))},
       {"pipeline_not_prewarmed",
        fmt::format("{}", g_fallback_counts[4].load(std::memory_order_relaxed))},
       {"route_runtime_shader_translations",
        fmt::format("{}",
                    g_runtime_shader_translations.load(
                        std::memory_order_relaxed))},
       {"route_runtime_sync_pipeline_creations",
        fmt::format("{}",
                    g_runtime_sync_pipeline_creations.load(
                        std::memory_order_relaxed))}});
  std::lock_guard lock(g_mutex);
  if (const auto pass = g_pass_tracker.Finish()) {
    RecordPassLocked(*pass);
  }
  const auto root = diagnostics::StateRoot() / "cache" / "fh1-gpu-corpus";
  std::error_code error;
  std::filesystem::create_directories(root, error);
  if (error) {
    diagnostics::RecordEvent("native_renderer.v4.corpus.write",
                             {{"status", "create_directory_failed"}});
    return;
  }
  const auto output = root / (diagnostics::SessionId() + ".json");
  const auto staging = output.string() + ".tmp";
  std::ofstream stream(staging, std::ios::binary | std::ios::trunc);
  if (!stream) {
    diagnostics::RecordEvent("native_renderer.v4.corpus.write",
                             {{"status", "open_failed"}});
    return;
  }
  stream << "{\n  \"schema\": \"pinyon-shift.fh1-gpu-corpus.v3\",\n"
         << "  \"key_version\": "
         << rex::system::GraphicsFh1ExecutionKey::kVersion << ",\n"
         << "  \"unique_keys\": " << g_entries.size() << ",\n"
         << "  \"unique_passes\": " << g_passes.size() << ",\n"
         << "  \"overflow\": " << g_overflow << ",\n"
         << "  \"collisions\": " << g_collisions << ",\n"
         << "  \"pass_collisions\": " << g_pass_collisions << ",\n"
         << "  \"entries\": [\n";
  bool first = true;
  for (const auto& [identity, entry] : g_entries) {
    if (!first) {
      stream << ",\n";
    }
    first = false;
    stream << fmt::format(
        "    {{\"identity\":\"{:016X}\",\"kind\":{},"
        "\"count\":{},\"first_frame\":{},\"last_frame\":{},"
        "\"index_count\":{},\"index_buffer_guest_base\":{},"
        "\"index_buffer_length\":{},"
        "\"vertex_shader\":\"{:016X}\",\"pixel_shader\":\"{:016X}\","
        "\"shader_state\":\"{:016X}\",\"pipeline_state\":\"{:016X}\","
        "\"attachment_state\":\"{:016X}\",\"resource_state\":\"{:016X}\","
        "\"dynamic_state\":\"{:016X}\",\"operation_state\":\"{:016X}\","
        "\"hazard_flags\":{},\"flags\":{}",
        identity, uint32_t(entry.key.kind), entry.count, entry.first_frame,
        entry.last_frame, entry.index_count, entry.index_buffer_guest_base,
        entry.index_buffer_length, entry.vertex_shader, entry.pixel_shader,
        entry.key.shader_state, entry.key.pipeline_state,
        entry.key.attachment_state, entry.key.resource_state,
        entry.key.dynamic_state, entry.key.operation_state,
        entry.key.hazard_flags, entry.key.flags);
    if (entry.has_copy) {
      const auto& copy = entry.copy;
      stream << fmt::format(
          ",\"copy\":{{\"written_address\":{},\"written_length\":{},"
          "\"rb_copy_control\":{},\"rb_copy_dest_base\":{},"
          "\"rb_copy_dest_info\":{},\"rb_copy_dest_pitch\":{},"
          "\"surface_info\":{},\"source_resource_width\":{},"
          "\"source_resource_height\":{},\"source_resource_format\":{},"
          "\"source_sample_count\":{},\"source_guest_msaa_samples\":{},"
          "\"draw_resolution_scale_x\":{},\"draw_resolution_scale_y\":{},"
          "\"source_target_base_tiles\":{},"
          "\"source_target_pitch_tiles_at_32bpp\":{},"
          "\"resolve_source_base_tiles\":{},"
          "\"resolve_source_pitch_tiles\":{},"
          "\"resolve_source_format\":{},"
          "\"resolve_source_guest_msaa_samples\":{},"
          "\"resolve_guest_offset_x\":{},\"resolve_guest_offset_y\":{},"
          "\"resolve_guest_width\":{},\"resolve_guest_height\":{},"
          "\"resolve_physical_offset_x\":{},"
          "\"resolve_physical_offset_y\":{},"
          "\"resolve_physical_width\":{},\"resolve_physical_height\":{},"
          "\"resolve_dest_offset_x\":{},\"resolve_dest_offset_y\":{},"
          "\"resolve_dest_pitch\":{},\"resolve_dest_height\":{},"
          "\"resolve_sample_select\":{},\"resolve_info_valid\":{},"
          "\"source_target_available\":{},\"native_2x_msaa\":{},"
          "\"succeeded\":{}}}",
          copy.written_address, copy.written_length, copy.rb_copy_control,
          copy.rb_copy_dest_base, copy.rb_copy_dest_info,
          copy.rb_copy_dest_pitch, copy.surface_info,
          copy.source_resource_width, copy.source_resource_height,
          copy.source_resource_format, copy.source_sample_count,
          copy.source_guest_msaa_samples, copy.draw_resolution_scale_x,
          copy.draw_resolution_scale_y, copy.source_target_base_tiles,
          copy.source_target_pitch_tiles_at_32bpp,
          copy.resolve_source_base_tiles, copy.resolve_source_pitch_tiles,
          copy.resolve_source_format,
          copy.resolve_source_guest_msaa_samples,
          copy.resolve_guest_offset_x, copy.resolve_guest_offset_y,
          copy.resolve_guest_width, copy.resolve_guest_height,
          copy.resolve_physical_offset_x, copy.resolve_physical_offset_y,
          copy.resolve_physical_width, copy.resolve_physical_height,
          copy.resolve_dest_offset_x, copy.resolve_dest_offset_y,
          copy.resolve_dest_pitch, copy.resolve_dest_height,
          copy.resolve_sample_select, copy.resolve_info_valid,
          copy.source_target_available, copy.native_2x_msaa,
          copy.succeeded);
    }
    stream << "}";
  }
  stream << "\n  ],\n  \"passes\": [\n";
  first = true;
  for (const auto& [signature, entry] : g_passes) {
    if (!first) {
      stream << ",\n";
    }
    first = false;
    stream << fmt::format(
        "    {{\"signature\":\"{:016X}\"," 
        "\"attachment_state\":\"{:016X}\"," 
        "\"first_draw_family\":\"{:016X}\"," 
        "\"first_draw_identity\":\"{:016X}\"," 
        "\"terminal_copy_state\":\"{:016X}\"," 
        "\"draw_count\":{},\"hazard_flags\":{},"
        "\"prepare_cpu_time_ns\":{},"
        "\"average_prepare_cpu_time_ns\":{},"
        "\"average_prepare_cpu_time_per_draw_ns\":{},"
        "\"occurrences\":{},\"draw_executions\":{},"
        "\"first_frame\":{},\"last_frame\":{}}}",
        signature, entry.summary.attachment_state,
        entry.summary.first_draw_family,
        entry.summary.first_draw_identity,
        entry.summary.terminal_copy_state, entry.summary.draw_count,
        entry.summary.hazard_flags, entry.summary.prepare_cpu_time_ns,
        entry.occurrences
            ? entry.summary.prepare_cpu_time_ns / entry.occurrences
            : 0,
        entry.draw_executions
            ? entry.summary.prepare_cpu_time_ns / entry.draw_executions
            : 0,
        entry.occurrences, entry.draw_executions, entry.first_frame,
        entry.last_frame);
  }
  stream << "\n  ]\n}\n";
  stream.close();
  if (!stream) {
    std::filesystem::remove(staging, error);
    diagnostics::RecordEvent("native_renderer.v4.corpus.write",
                             {{"status", "write_failed"}});
    return;
  }
  std::filesystem::rename(staging, output, error);
  diagnostics::RecordEvent(
      "native_renderer.v4.corpus.write",
      {{"status", error ? "commit_failed" : "written"},
       {"path", output.string()},
       {"unique_keys", fmt::format("{}", g_entries.size())},
       {"unique_passes", fmt::format("{}", g_passes.size())},
       {"overflow", fmt::format("{}", g_overflow)},
       {"collisions", fmt::format("{}", g_collisions)},
       {"pass_collisions", fmt::format("{}", g_pass_collisions)}});
}

}  // namespace pinyon_shift::native_renderer
