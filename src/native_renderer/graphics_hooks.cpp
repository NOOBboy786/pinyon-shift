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
};
thread_local std::vector<Snr01ProceduralScope> snr01_procedural_scopes;
thread_local uint64_t snr01_packet_count = 0;
thread_local uint64_t snr01_semantic_packet_count = 0;
thread_local uint64_t snr01_procedural_count = 0;
thread_local uint64_t snr01_unmatched_exits = 0;
constexpr uint64_t kSnr01PacketLimit = 8192;
constexpr uint64_t kSnr01ProceduralLimit = 4096;

bool Snr01TraceCurrentFrame() {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  return target > 0 && uint64_t(target) ==
                           uint64_t(rex::perf::GetTotalCounter(
                               rex::perf::CounterId::kSourceFrameCount));
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
      "\"procedural_receiver\":{},\"procedural_call\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, path, guest_address, guest_address & 0x1FFFFFFF,
      header_word, command_owner,
      snr01_procedural_scopes.empty()
          ? 0 : snr01_procedural_scopes.back().receiver,
      snr01_procedural_scopes.empty()
          ? 0 : snr01_procedural_scopes.back().ordinal);
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
  RecordFh1GpuExecution(observation);
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
  graphics_system->SetPreparedDrawObserver(enabled ? &ObservePreparedDraw
                                                   : nullptr);
  graphics_system->SetCopyObserver(enabled ? &ObserveCopy : nullptr);
}

void UninstallGraphicsCensus(rex::system::IGraphicsSystem* graphics_system) {
  if (graphics_system) {
    graphics_system->SetPreparedDrawObserver(nullptr);
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
        "\"procedural_calls\":{},\"unmatched_exits\":{},"
        "\"unfinished_scopes\":{},\"packet_limit\":{},\"scope_limit\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        snr01_packet_count, snr01_semantic_packet_count,
        snr01_procedural_count, snr01_unmatched_exits,
        snr01_procedural_scopes.size(), kSnr01PacketLimit, kSnr01ProceduralLimit);
  }
  snr01_procedural_scopes.clear();
  snr01_packet_count = snr01_semantic_packet_count =
      snr01_procedural_count = snr01_unmatched_exits = 0;
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

void PinyonShiftObserveProceduralItemBegin(PPCRegister& r3) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_procedural_count;
  snr01_procedural_scopes.push_back(
      {r3.u32, snr01_packet_count, snr01_semantic_packet_count, ordinal});
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
        "\"last_semantic_packet\":{},\"nested_depth\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.receiver, scope.first_packet + 1,
        snr01_packet_count, scope.first_semantic_packet + 1,
        snr01_semantic_packet_count, snr01_procedural_scopes.size());
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
