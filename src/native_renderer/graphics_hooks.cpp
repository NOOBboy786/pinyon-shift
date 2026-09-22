#include "native_renderer/graphics_hooks.h"

#include <array>
#include <atomic>
#include <chrono>
#include <mutex>
#include <set>
#include <thread>
#include <vector>

#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/ppc/context.h>

#include <rex/perf/counter.h>
#include <rex/system/interfaces/graphics.h>

#include "native_renderer/fh1_gpu_corpus.h"

REXCVAR_DEFINE_BOOL(pinyon_shift_fh1_clear_producer_trace, false, "Pinyon Shift",
                    "Record bounded guest clear-producer timing and shader copies")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_INT32(pinyon_shift_snr01_trace_source_frame, 0, "Pinyon Shift",
                     "Trace one source frame's procedural scopes and indexed PM4 headers")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);

namespace {

using ClearClock = std::chrono::steady_clock;
struct ClearProducerSample {
  uint32_t device, flags, rectangle, colour, stencil, stack;
  double depth;
  uint64_t frame;
  uint32_t shader_copies = 0, shader_bytes = 0, refills = 0;
  uint32_t first_shader_source = 0, first_shader_destination = 0;
  bool nested = false;
  ClearClock::time_point begin;
};
thread_local std::vector<ClearProducerSample> clear_producers;
std::atomic<uint64_t> clear_producer_records{0};

struct TitleEmitterSample {
  uint64_t frame;
  ClearClock::time_point begin;
};
thread_local std::vector<TitleEmitterSample> title_emitters;
thread_local uint64_t title_emitter_frame = 0;
thread_local uint64_t title_emitter_calls = 0;
thread_local uint64_t title_emitter_time_ns = 0;
thread_local uint64_t title_packet_count = 0;
thread_local int64_t title_first_packet_ns = 0;
thread_local int64_t title_last_packet_ns = 0;

struct Snr01ProceduralScope {
  uint32_t receiver;
  uint64_t first_packet;
  uint64_t first_semantic_packet;
  uint64_t ordinal;
  uint32_t descriptor_index = 0;
  uint32_t descriptor_address = 0;
  uint32_t descriptor_kind = 0;
  uint32_t render_state = 0;
  uint32_t runtime_address = 0;
  uint32_t submit_context = 0;
  uint32_t submit_primitive = 0;
  uint32_t submit_arg5 = 0;
  uint32_t submit_arg6 = 0;
  bool descriptor_seen = false;
  bool runtime_seen = false;
  bool submit_seen = false;
};
struct Snr01DispatchScope {
  uint32_t caller_lr;
  uint32_t receiver;
  uint32_t context;
  uint32_t arg5;
  uint32_t arg6;
  uint32_t arg7;
  uint32_t arg8;
  uint32_t arg9;
  uint32_t arg10;
  uint64_t first_semantic_packet;
  uint64_t first_procedural_call;
  uint64_t ordinal;
};
struct Snr01EmitterScope {
  uint32_t caller_lr;
  uint32_t owner;
  uint32_t arg4;
  uint32_t arg5;
  uint32_t arg6;
  uint64_t first_semantic_packet;
  uint64_t ordinal;
};
struct Snr01DirectScope {
  uint32_t caller_lr;
  uint32_t owner;
  uint32_t arg4;
  uint32_t arg5;
  uint32_t arg6;
  uint32_t arg7;
  uint64_t first_packet;
  uint64_t ordinal;
};
struct Snr01ViewScope {
  uint32_t view;
  uint32_t argument;
  uint64_t first_semantic_packet;
  uint64_t first_direct_packet;
  uint64_t first_primary_packet;
  uint64_t ordinal;
};
thread_local std::vector<Snr01EmitterScope> snr01_emitter_scopes;
thread_local std::vector<Snr01DirectScope> snr01_direct_scopes;
thread_local std::vector<Snr01ViewScope> snr01_view_scopes;
thread_local std::vector<uint32_t> snr01_primary_indirect_callers;
thread_local std::vector<uint32_t> snr01_queued_indirect_callers;
thread_local std::vector<Snr01DispatchScope> snr01_dispatch_scopes;
thread_local std::vector<Snr01DispatchScope> snr01_render_state_scopes;
thread_local std::vector<Snr01ProceduralScope> snr01_procedural_scopes;
thread_local uint64_t snr01_packet_count = 0;
thread_local uint64_t snr01_semantic_packet_count = 0;
thread_local uint64_t snr01_procedural_count = 0;
thread_local uint64_t snr01_dispatch_count = 0;
thread_local uint64_t snr01_render_state_count = 0;
thread_local uint64_t snr01_emitter_count = 0;
thread_local uint64_t snr01_state_wrapper_count = 0;
thread_local uint64_t snr01_dispatch_wrapper_count = 0;
thread_local uint64_t snr01_track75_count = 0;
thread_local uint64_t snr01_track79_count = 0;
thread_local uint64_t snr01_track_pass_count = 0;
thread_local uint64_t snr01_view_begin_count = 0;
thread_local uint64_t snr01_view_selected_count = 0;
thread_local uint64_t snr01_view_track_count = 0;
thread_local uint64_t snr01_direct_call_count = 0;
thread_local uint64_t snr01_direct_packet_count = 0;
thread_local uint64_t snr01_primary_indirect_packet_count = 0;
thread_local uint64_t snr01_unmatched_direct_exits = 0;
thread_local uint64_t snr01_unmatched_emitter_exits = 0;
thread_local uint64_t snr01_unmatched_dispatch_exits = 0;
thread_local uint64_t snr01_unmatched_render_state_exits = 0;
thread_local uint64_t snr01_unmatched_exits = 0;
constexpr uint64_t kSnr01PacketLimit = 8192;
constexpr uint64_t kSnr01ProceduralLimit = 4096;

bool Snr01TraceCurrentFrame() {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  return target > 0 && uint64_t(target) ==
                           uint64_t(rex::perf::GetTotalCounter(
                               rex::perf::CounterId::kSourceFrameCount));
}

bool Snr01TracePrimaryIndirectFrame() {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  const uint64_t frame = rex::perf::GetTotalCounter(
      rex::perf::CounterId::kSourceFrameCount);
  return target > 0 && frame >= uint64_t(target) &&
         frame <= uint64_t(target) + 1;
}

void RecordSnr01SemanticPacket(const char* path, uint32_t previous_word,
                               uint32_t header_word, uint32_t command_owner) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_semantic_packet_count;
  if (ordinal > kSnr01PacketLimit) {
    return;
  }
  const uint32_t guest_address = previous_word + 4;
  REXGPU_INFO(
      "FH1 SNR01 semantic packet {{\"frame\":{},\"ordinal\":{},"
      "\"path\":\"{}\",\"header_guest\":{},\"header_physical\":{},"
      "\"header_word\":{},\"command_owner\":{},"
      "\"procedural_receiver\":{},\"procedural_call\":{},"
      "\"dispatch_receiver\":{},\"dispatch_call\":{},"
      "\"render_state_receiver\":{},\"render_state_call\":{},"
      "\"emitter_call\":{},\"emitter_caller_lr\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, path, guest_address, guest_address & 0x1FFFFFFF,
      header_word, command_owner,
      snr01_procedural_scopes.empty()
          ? 0 : snr01_procedural_scopes.back().receiver,
      snr01_procedural_scopes.empty()
          ? 0 : snr01_procedural_scopes.back().ordinal,
      snr01_dispatch_scopes.empty()
          ? 0 : snr01_dispatch_scopes.back().receiver,
      snr01_dispatch_scopes.empty()
          ? 0 : snr01_dispatch_scopes.back().ordinal,
      snr01_render_state_scopes.empty()
          ? 0 : snr01_render_state_scopes.back().receiver,
      snr01_render_state_scopes.empty()
          ? 0 : snr01_render_state_scopes.back().ordinal,
      snr01_emitter_scopes.empty()
          ? 0 : snr01_emitter_scopes.back().ordinal,
      snr01_emitter_scopes.empty()
          ? 0 : snr01_emitter_scopes.back().caller_lr);
}

void RecordSnr01DirectPacket(const char* path, uint32_t previous_word,
                             uint32_t header_word, uint32_t command_owner) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_direct_packet_count;
  if (ordinal > kSnr01PacketLimit) {
    return;
  }
  const uint32_t guest_address = previous_word + 4;
  REXGPU_INFO(
      "FH1 SNR01 direct packet {{\"frame\":{},\"ordinal\":{},"
      "\"path\":\"{}\",\"header_guest\":{},"
      "\"header_physical\":{},\"header_word\":{},"
      "\"command_owner\":{},\"direct_call\":{},"
      "\"direct_caller_lr\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, path, guest_address, guest_address & 0x1FFFFFFF,
      header_word, command_owner,
      snr01_direct_scopes.empty() ? 0 : snr01_direct_scopes.back().ordinal,
      snr01_direct_scopes.empty() ? 0 : snr01_direct_scopes.back().caller_lr);
}

bool ClearProducerTraceEnabled() {
  static const bool enabled = REXCVAR_GET(pinyon_shift_fh1_clear_producer_trace);
  return enabled;
}

}  // namespace

namespace pinyon_shift::native_renderer {
namespace {

void ObservePreparedDraw(
    const rex::system::GraphicsPreparedDrawObservation& observation) {
  static const bool corpus_enabled =
      rex::cvar::GetFlagByName("pinyon_shift_fh1_gpu_corpus") == "true";
  if (corpus_enabled) {
    RecordFh1GpuExecution(observation);
  }
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  if (target <= 0 || observation.frame_sequence + 1 < uint64_t(target) ||
      observation.frame_sequence > uint64_t(target) + 1) {
    return;
  }
  static thread_local uint64_t logged_frame = 0;
  static thread_local uint64_t logged_draws = 0;
  if (logged_frame != observation.frame_sequence) {
    logged_frame = observation.frame_sequence;
    logged_draws = 0;
  }
  if (++logged_draws > kSnr01PacketLimit) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 prepared draw {{\"frame\":{},\"ordinal\":{},"
      "\"indirect_execution\":{},\"indirect_parent\":{},"
      "\"dispatch_packet_physical\":{},"
      "\"packet_physical\":{},\"command_buffer\":{},"
      "\"command_bytes\":{},\"draw_end_offset\":{},\"vertex_shader\":{},"
      "\"pixel_shader\":{},\"index_count\":{},"
      "\"render_target_bits\":{}}}",
      observation.frame_sequence, logged_draws,
      observation.indirect_buffer_execution_id,
      observation.indirect_buffer_parent_execution_id,
      observation.indirect_dispatch_packet_physical_address,
      observation.draw_packet_physical_address,
      observation.command_buffer_physical_address,
      observation.command_buffer_bytes,
      observation.command_buffer_end_offset, observation.vertex_shader_hash,
      observation.pixel_shader_hash, observation.index_count,
      observation.bound_render_target_bits);
}

void ObserveIndirectBuffer(
    const rex::system::GraphicsIndirectBufferObservation& observation) {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  if (target <= 0 || observation.frame_sequence + 1 < uint64_t(target) ||
      observation.frame_sequence > uint64_t(target) + 1) {
    return;
  }
  static thread_local uint64_t logged_frame = 0;
  static thread_local uint64_t logged_buffers = 0;
  if (logged_frame != observation.frame_sequence) {
    logged_frame = observation.frame_sequence;
    logged_buffers = 0;
  }
  if (++logged_buffers > kSnr01PacketLimit) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 indirect buffer {{\"frame\":{},\"ordinal\":{},"
      "\"execution\":{},\"parent\":{},\"dispatch_packet_physical\":{},"
      "\"command_buffer\":{},\"command_bytes\":{}}}",
      observation.frame_sequence, logged_buffers, observation.execution_id,
      observation.parent_execution_id,
      observation.dispatch_packet_physical_address,
      observation.command_buffer_physical_address,
      observation.command_buffer_bytes);
}

void ObserveCopy(const rex::system::GraphicsCopyObservation& observation) {
  RecordFh1GpuCopy(observation);
}

}  // namespace

void InstallGraphicsCensus(rex::system::IGraphicsSystem* graphics_system,
                           rex::memory::Memory*) {
  if (!graphics_system) {
    return;
  }
  const bool enabled = ResetFh1GpuCorpus();
  graphics_system->SetPreparedDrawObserver(
      enabled || REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) > 0
          ? &ObservePreparedDraw
          : nullptr);
  graphics_system->SetIndirectBufferObserver(
      REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) > 0
          ? &ObserveIndirectBuffer
          : nullptr);
  graphics_system->SetCopyObserver(enabled ? &ObserveCopy : nullptr);
}

void UninstallGraphicsCensus(rex::system::IGraphicsSystem* graphics_system) {
  if (graphics_system) {
    graphics_system->SetPreparedDrawObserver(nullptr);
    graphics_system->SetIndirectBufferObserver(nullptr);
    graphics_system->SetCopyObserver(nullptr);
  }
  FlushFh1GpuCorpus();
}

}  // namespace pinyon_shift::native_renderer

// FH1's sole VdSwap call is the source-frame boundary used by the real-frame
// presentation and performance gates. It intentionally changes no guest state.
void PinyonShiftObserveGraphicsFrame() {
  if (Snr01TraceCurrentFrame()) {
    REXGPU_INFO(
        "FH1 SNR01 summary {{\"frame\":{},\"indexed_packets\":{},"
        "\"semantic_packets\":{},"
        "\"procedural_calls\":{},\"dispatch_calls\":{},"
        "\"render_state_calls\":{},\"emitter_calls\":{},"
        "\"state_wrapper_calls\":{},\"dispatch_wrapper_calls\":{},"
        "\"track75_calls\":{},\"track79_calls\":{},"
        "\"track_pass_calls\":{},"
        "\"direct_calls_swap_thread\":{},"
        "\"draw_header_packets_swap_thread\":{},"
        "\"unmatched_direct_exits_swap_thread\":{},"
        "\"unfinished_direct_scopes_swap_thread\":{},"
        "\"unmatched_exits\":{},"
        "\"unmatched_dispatch_exits\":{},"
        "\"unmatched_render_state_exits\":{},"
        "\"unmatched_emitter_exits\":{},"
        "\"unfinished_scopes\":{},\"unfinished_dispatch_scopes\":{},"
        "\"unfinished_render_state_scopes\":{},"
        "\"unfinished_emitter_scopes\":{},"
        "\"packet_limit\":{},\"scope_limit\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        snr01_packet_count, snr01_semantic_packet_count,
        snr01_procedural_count, snr01_dispatch_count,
        snr01_render_state_count, snr01_emitter_count,
        snr01_state_wrapper_count, snr01_dispatch_wrapper_count,
        snr01_track75_count, snr01_track79_count,
        snr01_track_pass_count,
        snr01_direct_call_count, snr01_direct_packet_count,
        snr01_unmatched_direct_exits, snr01_direct_scopes.size(),
        snr01_unmatched_exits,
        snr01_unmatched_dispatch_exits,
        snr01_unmatched_render_state_exits,
        snr01_unmatched_emitter_exits,
        snr01_procedural_scopes.size(), snr01_dispatch_scopes.size(),
        snr01_render_state_scopes.size(),
        snr01_emitter_scopes.size(),
        kSnr01PacketLimit, kSnr01ProceduralLimit);
  }
  snr01_emitter_scopes.clear();
  snr01_direct_scopes.clear();
  snr01_dispatch_scopes.clear();
  snr01_render_state_scopes.clear();
  snr01_procedural_scopes.clear();
  snr01_packet_count = snr01_semantic_packet_count =
      snr01_procedural_count = snr01_dispatch_count =
      snr01_render_state_count = snr01_unmatched_exits =
      snr01_unmatched_dispatch_exits =
      snr01_unmatched_render_state_exits = snr01_emitter_count =
      snr01_unmatched_emitter_exits = snr01_state_wrapper_count =
      snr01_dispatch_wrapper_count = snr01_track75_count =
      snr01_track79_count = snr01_track_pass_count =
      snr01_direct_call_count = snr01_direct_packet_count =
      snr01_unmatched_direct_exits = 0;
  if (rex::perf::CriticalPathTraceEnabled() &&
      (title_emitter_calls || title_packet_count)) {
    rex::perf::TraceCriticalPath("title_emitter", int64_t(title_emitter_frame),
                                 int64_t(title_emitter_time_ns),
                                 int64_t(title_emitter_calls));
    rex::perf::TraceCriticalPath("pm4_publish", int64_t(title_emitter_frame),
                                 int64_t(title_packet_count), title_first_packet_ns,
                                 title_last_packet_ns);
  }
  PROFILE_SOURCE_FRAME();
  title_emitter_frame = uint64_t(rex::perf::GetTotalCounter(
      rex::perf::CounterId::kSourceFrameCount));
  title_emitter_calls = title_emitter_time_ns = title_packet_count = 0;
  title_first_packet_ns = title_last_packet_ns = 0;
  rex::perf::TraceCriticalPath("source_frame", int64_t(title_emitter_frame));
}

void PinyonShiftObserveTitleDrawEmitterBegin() {
  if (rex::perf::CriticalPathTraceEnabled()) {
    title_emitters.push_back({uint64_t(rex::perf::GetTotalCounter(
                                  rex::perf::CounterId::kSourceFrameCount)),
                              ClearClock::now()});
  }
}

void PinyonShiftObserveTitleDrawEmitterEnd() {
  if (!rex::perf::CriticalPathTraceEnabled() || title_emitters.empty()) {
    return;
  }
  const auto sample = title_emitters.back();
  title_emitters.pop_back();
  title_emitter_frame = sample.frame;
  ++title_emitter_calls;
  title_emitter_time_ns += uint64_t(
      std::chrono::duration_cast<std::chrono::nanoseconds>(ClearClock::now() -
                                                           sample.begin)
          .count());
}

void PinyonShiftObserveTitleDrawPacketPublish(PPCRegister& r3, PPCRegister& r11,
                                             PPCRegister& r31) {
  if (Snr01TraceCurrentFrame()) {
    const uint64_t ordinal = ++snr01_packet_count;
    if (ordinal <= kSnr01PacketLimit) {
      const uint32_t guest_address = r3.u32 + 4;
      REXGPU_INFO(
          "FH1 SNR01 indexed packet {{\"frame\":{},\"ordinal\":{},"
          "\"header_guest\":{},\"header_physical\":{},"
          "\"header_word\":{},\"command_owner\":{},"
          "\"procedural_receiver\":{},\"procedural_call\":{}}}",
          rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
          ordinal, guest_address, guest_address & 0x1FFFFFFF, r11.u32,
          r31.u32, snr01_procedural_scopes.empty()
                       ? 0 : snr01_procedural_scopes.back().receiver,
          snr01_procedural_scopes.empty()
                       ? 0 : snr01_procedural_scopes.back().ordinal);
    }
  }
  if (!rex::perf::CriticalPathTraceEnabled()) {
    return;
  }
  const int64_t now_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                             ClearClock::now().time_since_epoch())
                             .count();
  if (!title_packet_count) {
    title_first_packet_ns = now_ns;
  }
  title_last_packet_ns = now_ns;
  ++title_packet_count;
}

void PinyonShiftObservePresentationViewBegin(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_view_begin_count;
  snr01_view_scopes.push_back(
      {r3.u32, r4.u32, snr01_semantic_packet_count,
       snr01_direct_packet_count, snr01_primary_indirect_packet_count,
       ordinal});
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 view begin {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"view\":{},\"arg4\":{},\"arg5\":{},"
        "\"arg6\":{},\"arg7\":{},\"arg8\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32, r7.u32,
        r8.u32);
  }
}

void PinyonShiftObservePresentationViewEnd() {
  if (snr01_view_scopes.empty()) {
    return;
  }
  const auto scope = snr01_view_scopes.back();
  snr01_view_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 view end {{\"frame\":{},\"call\":{},"
        "\"view\":{},\"arg4\":{},"
        "\"first_semantic\":{},\"last_semantic\":{},"
        "\"first_direct\":{},\"last_direct\":{},"
        "\"first_primary\":{},\"last_primary\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.view, scope.argument,
        scope.first_semantic_packet + 1, snr01_semantic_packet_count,
        scope.first_direct_packet + 1, snr01_direct_packet_count,
        scope.first_primary_packet + 1,
        snr01_primary_indirect_packet_count);
  }
}

void PinyonShiftObservePresentationViewSelected(PPCRegister& r31,
                                                PPCRegister& r25) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_view_selected_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 view selected {{\"frame\":{},\"call\":{},"
        "\"view\":{},\"selected_context\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r31.u32, r25.u32);
  }
}

void PinyonShiftObservePresentationTrackLink(PPCRegister& r31,
                                             PPCRegister& r11,
                                             PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_view_track_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 view track link {{\"frame\":{},\"call\":{},"
        "\"view\":{},\"view_state\":{},\"track_presenter\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r31.u32, r11.u32, r10.u32);
  }
}

void PinyonShiftObserveTrackPresentation75(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8, PPCRegister& r9,
    PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_track75_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 track presentation {{\"frame\":{},\"slot\":75,"
        "\"call\":{},\"caller_lr\":{},\"receiver\":{},"
        "\"arg4\":{},\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"arg8\":{},\"arg9\":{},\"arg10\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
        r7.u32, r8.u32, r9.u32, r10.u32);
  }
}

void PinyonShiftObserveTrackPresentation79(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8, PPCRegister& r9,
    PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_track79_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 track presentation {{\"frame\":{},\"slot\":79,"
        "\"call\":{},\"caller_lr\":{},\"receiver\":{},"
        "\"arg4\":{},\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"arg8\":{},\"arg9\":{},\"arg10\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
        r7.u32, r8.u32, r9.u32, r10.u32);
  }
}

void PinyonShiftObserveTrackPassCaller(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_track_pass_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 track pass caller {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"receiver\":{},\"arg4\":{},"
        "\"arg5\":{},\"arg6\":{},\"arg7\":{},\"arg8\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
        r7.u32, r8.u32);
  }
}

void PinyonShiftObserveProceduralStateWrapperCaller(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8, PPCRegister& r9) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_state_wrapper_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 state wrapper {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"arg3\":{},\"arg4\":{},\"arg5\":{},"
        "\"arg6\":{},\"arg7\":{},\"arg8\":{},\"arg9\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
        r7.u32, r8.u32, r9.u32);
  }
}

void PinyonShiftObserveProceduralDispatchWrapperCaller(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8, PPCRegister& r9,
    PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_dispatch_wrapper_count;
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 dispatch wrapper {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"arg3\":{},\"arg4\":{},\"arg5\":{},"
        "\"arg6\":{},\"arg7\":{},\"arg8\":{},\"arg9\":{},"
        "\"arg10\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
        r7.u32, r8.u32, r9.u32, r10.u32);
  }
}

void PinyonShiftObserveProceduralDispatchBegin(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8, PPCRegister& r9,
    PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_dispatch_count;
  snr01_dispatch_scopes.push_back(
      {r12.u32, r3.u32, r4.u32, r5.u32, r6.u32, r7.u32, r8.u32,
       r9.u32, r10.u32,
       snr01_semantic_packet_count, snr01_procedural_count, ordinal});
}

void PinyonShiftObserveProceduralDispatchEnd() {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  if (snr01_dispatch_scopes.empty()) {
    ++snr01_unmatched_dispatch_exits;
    return;
  }
  const auto scope = snr01_dispatch_scopes.back();
  snr01_dispatch_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 procedural dispatch {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"receiver\":{},\"context\":{},"
        "\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"arg8\":{},\"arg9\":{},\"arg10\":{},"
        "\"first_semantic_packet\":{},\"last_semantic_packet\":{},"
        "\"first_item_call\":{},\"last_item_call\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.caller_lr, scope.receiver, scope.context,
        scope.arg5, scope.arg6, scope.arg7,
        scope.arg8, scope.arg9, scope.arg10,
        scope.first_semantic_packet + 1, snr01_semantic_packet_count,
        scope.first_procedural_call + 1, snr01_procedural_count);
  }
}

void PinyonShiftObserveProceduralRenderStateBegin(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7, PPCRegister& r8, PPCRegister& r9,
    PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_render_state_count;
  snr01_render_state_scopes.push_back(
      {r12.u32, r3.u32, r4.u32, r5.u32, r6.u32, r7.u32, r8.u32,
       r9.u32, r10.u32,
       snr01_semantic_packet_count, snr01_procedural_count, ordinal});
}

void PinyonShiftObserveProceduralRenderStateEnd() {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  if (snr01_render_state_scopes.empty()) {
    ++snr01_unmatched_render_state_exits;
    return;
  }
  const auto scope = snr01_render_state_scopes.back();
  snr01_render_state_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 render state {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"receiver\":{},\"context\":{},"
        "\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"arg8\":{},\"arg9\":{},\"arg10\":{},"
        "\"first_semantic_packet\":{},\"last_semantic_packet\":{},"
        "\"first_item_call\":{},\"last_item_call\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.caller_lr, scope.receiver, scope.context,
        scope.arg5, scope.arg6, scope.arg7,
        scope.arg8, scope.arg9, scope.arg10,
        scope.first_semantic_packet + 1, snr01_semantic_packet_count,
        scope.first_procedural_call + 1, snr01_procedural_count);
  }
}

void PinyonShiftObserveProceduralItemBegin(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r7, PPCRegister& r8,
    PPCRegister& r9, PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_procedural_count;
  snr01_procedural_scopes.push_back(
      {r3.u32, snr01_packet_count, snr01_semantic_packet_count, ordinal});
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 item arguments {{\"frame\":{},\"call\":{},"
        "\"receiver\":{},\"context\":{},\"arg7\":{},\"arg8\":{},"
        "\"arg9\":{},\"arg10\":{},\"dispatch_call\":{},"
        "\"render_state_call\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, r3.u32, r4.u32, r7.u32, r8.u32, r9.u32, r10.u32,
        snr01_dispatch_scopes.empty() ? 0
                                     : snr01_dispatch_scopes.back().ordinal,
        snr01_render_state_scopes.empty()
            ? 0 : snr01_render_state_scopes.back().ordinal);
  }
}

void PinyonShiftObserveProceduralDescriptor(PPCRegister& r9,
                                            PPCRegister& r28,
                                            PPCRegister& r8,
                                            PPCRegister& r25) {
  if (!Snr01TraceCurrentFrame() || snr01_procedural_scopes.empty()) {
    return;
  }
  auto& scope = snr01_procedural_scopes.back();
  scope.descriptor_index = r9.u32;
  scope.descriptor_address = r28.u32;
  scope.descriptor_kind = r8.u32;
  scope.render_state = r25.u32;
  scope.descriptor_seen = true;
}

void PinyonShiftObserveProceduralRuntimeRecord(PPCRegister& r26) {
  if (!Snr01TraceCurrentFrame() || snr01_procedural_scopes.empty()) {
    return;
  }
  auto& scope = snr01_procedural_scopes.back();
  scope.runtime_address = r26.u32;
  scope.runtime_seen = true;
}

void PinyonShiftObserveProceduralGeometrySubmit(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6) {
  if (!Snr01TraceCurrentFrame() || snr01_procedural_scopes.empty()) {
    return;
  }
  auto& scope = snr01_procedural_scopes.back();
  scope.submit_context = r3.u32;
  scope.submit_primitive = r4.u32;
  scope.submit_arg5 = r5.u32;
  scope.submit_arg6 = r6.u32;
  scope.submit_seen = true;
}

void PinyonShiftObserveProceduralItemEnd() {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  if (snr01_procedural_scopes.empty()) {
    ++snr01_unmatched_exits;
    return;
  }
  const auto scope = snr01_procedural_scopes.back();
  snr01_procedural_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 procedural item {{\"frame\":{},\"call\":{},"
        "\"receiver\":{},\"first_indexed_packet\":{},"
        "\"last_indexed_packet\":{},\"first_semantic_packet\":{},"
        "\"last_semantic_packet\":{},\"nested_depth\":{},"
        "\"descriptor_seen\":{},\"descriptor_index\":{},"
        "\"descriptor_address\":{},\"descriptor_kind\":{},"
        "\"render_state\":{},\"runtime_seen\":{},"
        "\"runtime_address\":{},\"submit_seen\":{},"
        "\"submit_context\":{},\"submit_primitive\":{},"
        "\"submit_arg5\":{},\"submit_arg6\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.receiver, scope.first_packet + 1,
        snr01_packet_count, scope.first_semantic_packet + 1,
        snr01_semantic_packet_count, snr01_procedural_scopes.size(),
        scope.descriptor_seen, scope.descriptor_index,
        scope.descriptor_address, scope.descriptor_kind, scope.render_state,
        scope.runtime_seen, scope.runtime_address, scope.submit_seen,
        scope.submit_context, scope.submit_primitive,
        scope.submit_arg5, scope.submit_arg6);
  }
}

void PinyonShiftObserveProceduralEmitterBegin(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_emitter_count;
  snr01_emitter_scopes.push_back(
      {r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
       snr01_semantic_packet_count, ordinal});
}

void PinyonShiftObserveProceduralEmitterEnd() {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  if (snr01_emitter_scopes.empty()) {
    ++snr01_unmatched_emitter_exits;
    return;
  }
  const auto scope = snr01_emitter_scopes.back();
  snr01_emitter_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 emitter {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"owner\":{},\"arg4\":{},"
        "\"arg5\":{},\"arg6\":{},"
        "\"first_semantic_packet\":{},\"last_semantic_packet\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.caller_lr, scope.owner, scope.arg4,
        scope.arg5, scope.arg6, scope.first_semantic_packet + 1,
        snr01_semantic_packet_count);
  }
}

void PinyonShiftObserveProceduralDrawPacketPrimary(PPCRegister& r30,
                                                  PPCRegister& r11,
                                                  PPCRegister& r31) {
  RecordSnr01SemanticPacket("primary", r30.u32, r11.u32, r31.u32);
}

void PinyonShiftObserveProceduralDrawPacketSecondary(PPCRegister& r6,
                                                    PPCRegister& r9,
                                                    PPCRegister& r31) {
  RecordSnr01SemanticPacket("secondary", r6.u32, r9.u32, r31.u32);
}

void PinyonShiftObserveDirectIndexedBegin(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r6, PPCRegister& r7) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_direct_call_count;
  snr01_direct_scopes.push_back(
      {r12.u32, r3.u32, r4.u32, r5.u32, r6.u32, r7.u32,
       snr01_direct_packet_count, ordinal});
}

void PinyonShiftObserveDirectIndexedPacketPrimary(
    PPCRegister& r25, PPCRegister& r11, PPCRegister& r31) {
  RecordSnr01DirectPacket("primary", r25.u32, r11.u32, r31.u32);
}

void PinyonShiftObserveDirectIndexedPacketSecondary(
    PPCRegister& r5, PPCRegister& r9, PPCRegister& r31) {
  RecordSnr01DirectPacket("secondary", r5.u32, r9.u32, r31.u32);
}

void PinyonShiftObserveDirectIndexedEnd() {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  if (snr01_direct_scopes.empty()) {
    ++snr01_unmatched_direct_exits;
    return;
  }
  const auto scope = snr01_direct_scopes.back();
  snr01_direct_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 direct call {{\"frame\":{},\"call\":{},"
        "\"caller_lr\":{},\"owner\":{},\"arg4\":{},"
        "\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"first_packet\":{},\"last_packet\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.caller_lr, scope.owner, scope.arg4,
        scope.arg5, scope.arg6, scope.arg7, scope.first_packet + 1,
        snr01_direct_packet_count);
  }
}

void PinyonShiftObserveIndexed2PacketPrimary(PPCRegister& r30,
                                             PPCRegister& r11,
                                             PPCRegister& r31) {
  RecordSnr01DirectPacket("indexed2_primary", r30.u32, r11.u32, r31.u32);
}

void PinyonShiftObserveQueuedIndirectBegin(
    PPCRegister& r12, PPCRegister&, PPCRegister&, PPCRegister&, PPCRegister&,
    PPCRegister&, PPCRegister&, PPCRegister&) {
  if (Snr01TracePrimaryIndirectFrame()) {
    snr01_queued_indirect_callers.push_back(r12.u32);
  }
}

void PinyonShiftObserveQueuedIndirectEnd() {
  if (!snr01_queued_indirect_callers.empty()) {
    snr01_queued_indirect_callers.pop_back();
  }
}

void PinyonShiftObservePrimaryIndirectBegin(PPCRegister& r12, PPCRegister&,
                                           PPCRegister&, PPCRegister&) {
  if (Snr01TracePrimaryIndirectFrame()) {
    snr01_primary_indirect_callers.push_back(r12.u32);
  }
}

void PinyonShiftObservePrimaryIndirectPacket(
    PPCRegister& r10, PPCRegister& r11, PPCRegister& r28, PPCRegister& r29,
    PPCRegister& r31, PPCRegister& r27, PPCRegister& r24, PPCRegister& r25,
    PPCRegister& r26, PPCRegister& r21) {
  if (!Snr01TracePrimaryIndirectFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_primary_indirect_packet_count;
  if (ordinal > kSnr01PacketLimit) {
    return;
  }
  const uint32_t guest_address = r28.u32 + r11.u32 * sizeof(uint32_t);
  REXGPU_INFO(
      "FH1 SNR01 primary indirect packet {{\"frame\":{},\"ordinal\":{},"
      "\"header_physical\":{},\"header_word\":{},\"gpu_target\":{},"
      "\"device\":{},\"entry_array\":{},\"entry_count\":{},"
      "\"entry_index\":{},\"ring_mask\":{},\"mode\":{},"
      "\"caller_lr\":{},\"queued_caller_lr\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, guest_address & 0x1FFFFFFF, r10.u32, r31.u32, r27.u32,
      r24.u32, r25.u32, r26.u32, r29.u32, r21.u32,
      snr01_primary_indirect_callers.empty()
          ? 0
          : snr01_primary_indirect_callers.back(),
      snr01_queued_indirect_callers.empty()
          ? 0
          : snr01_queued_indirect_callers.back());
}

void PinyonShiftObservePrimaryIndirectEnd() {
  if (!snr01_primary_indirect_callers.empty()) {
    snr01_primary_indirect_callers.pop_back();
  }
}

void PinyonShiftObserveIndexed2PacketSecondary(PPCRegister& r6,
                                               PPCRegister& r9,
                                               PPCRegister& r31) {
  RecordSnr01DirectPacket("indexed2_secondary", r6.u32, r9.u32, r31.u32);
}

void PinyonShiftObserveIndexed3PacketPrimary(PPCRegister& r30,
                                             PPCRegister& r11,
                                             PPCRegister& r31) {
  RecordSnr01DirectPacket("indexed3_primary", r30.u32, r11.u32, r31.u32);
}

void PinyonShiftObserveIndexed3PacketSecondary(PPCRegister& r5,
                                               PPCRegister& r9,
                                               PPCRegister& r31) {
  RecordSnr01DirectPacket("indexed3_secondary", r5.u32, r9.u32, r31.u32);
}

void PinyonShiftObserveSwapDrawPacket(PPCRegister& r9, PPCRegister& r10,
                                      PPCRegister& r31) {
  RecordSnr01DirectPacket("swap", r9.u32, r10.u32, r31.u32);
}

// Read-only hooks at the checked producer entry/common epilogue. Logging is
// outside the measured interval. Nested calls are explicit because their
// observation overhead is included in the parent's elapsed wall time.
void PinyonShiftObserveClearProducerBegin(PPCRegister& r3, PPCRegister& r4,
                                         PPCRegister& r5, PPCRegister& r6,
                                         PPCRegister& r8, PPCRegister& r1,
                                         PPCRegister& f1) {
  if (!ClearProducerTraceEnabled()) {
    return;
  }
  if (!clear_producers.empty()) {
    clear_producers.back().nested = true;
  }
  ClearProducerSample sample{r3.u32, r4.u32, r5.u32, r6.u32, r8.u32, r1.u32,
                             f1.f64, static_cast<uint64_t>(rex::perf::GetTotalCounter(
                                         rex::perf::CounterId::kSourceFrameCount))};
  clear_producers.push_back(sample);
  clear_producers.back().begin = ClearClock::now();
}

void PinyonShiftObserveClearShaderCopy(PPCRegister& r3, PPCRegister& r4,
                                      PPCRegister& r5) {
  if (!ClearProducerTraceEnabled() || clear_producers.empty()) {
    return;
  }
  auto& sample = clear_producers.back();
  if (!sample.shader_copies) {
    sample.first_shader_source = r4.u32;
    sample.first_shader_destination = r3.u32;
  }
  ++sample.shader_copies;
  sample.shader_bytes += r5.u32;
}

void PinyonShiftObserveClearCommandRefill() {
  if (ClearProducerTraceEnabled() && !clear_producers.empty()) {
    ++clear_producers.back().refills;
  }
}

void PinyonShiftObserveClearProducerEnd(PPCRegister& r31, PPCRegister& r1) {
  if (!ClearProducerTraceEnabled()) {
    return;
  }
  const auto end = ClearClock::now();
  const auto record = clear_producer_records.fetch_add(1, std::memory_order_relaxed);
  // ponytail: cap verbose records at 100,000; use aggregates for longer traces.
  if (clear_producers.empty() || clear_producers.back().device != r31.u32 ||
      clear_producers.back().stack != r1.u32 + 256) {
    clear_producers.clear();
    if (record < 100000) {
      REXGPU_INFO("FH1 clear producer unmatched end device={} stack={}",
                  r31.u32, r1.u32);
    }
    return;
  }
  const auto sample = clear_producers.back();
  clear_producers.pop_back();
  if (record >= 100000) {
    if (record == 100000) {
      REXGPU_INFO("FH1 clear producer record limit reached");
    }
    return;
  }
  REXGPU_INFO(
      "FH1 clear producer {{\"record\":{},\"thread\":{},\"frame\":{},"
      "\"device\":{},\"flags\":{},\"rectangle\":{},\"colour\":{},"
      "\"stencil\":{},\"depth\":{},\"elapsed_ns\":{},\"shader_copies\":{},"
      "\"shader_bytes\":{},\"first_shader_source\":{},"
      "\"first_shader_destination\":{},\"refills\":{},\"nested\":{}}}",
      record, std::hash<std::thread::id>{}(std::this_thread::get_id()), sample.frame,
      sample.device, sample.flags, sample.rectangle, sample.colour, sample.stencil,
      sample.depth, std::chrono::duration_cast<std::chrono::nanoseconds>(end - sample.begin).count(),
      sample.shader_copies, sample.shader_bytes, sample.first_shader_source,
      sample.first_shader_destination, sample.refills, sample.nested);
}

void PinyonShiftObserveSceneCommandBuffer(PPCRegister& r24, PPCRegister& r10,
                                         PPCRegister& r11) {
  static const bool enabled =
      rex::cvar::GetFlagByName("pinyon_shift_fh1_gpu_corpus") == "true" &&
      rex::cvar::GetFlagByName("pinyon_shift_fh1_scene_dump") == "true";
  if (!enabled) {
    return;
  }
  static std::mutex mutex;
  static std::set<std::array<uint32_t, 3>> observed;
  std::lock_guard lock(mutex);
  const std::array<uint32_t, 3> key = {r24.u32, r10.u32, r11.u32};
  if (observed.size() == 4096 || !observed.insert(key).second) {
    return;
  }
  REXGPU_INFO("FH1 scene producer {{\"object\":{},\"target\":{},\"words\":{}}}",
              r24.u32, r10.u32, r11.u32);
  if (observed.size() == 4096) {
    REXGPU_INFO("FH1 scene producer record limit reached");
  }
}
