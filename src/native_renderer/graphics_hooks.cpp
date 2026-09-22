#include "native_renderer/graphics_hooks.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <map>
#include <mutex>
#include <set>
#include <thread>
#include <vector>

#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/memory/utils.h>
#include <rex/ppc/context.h>

#include <rex/perf/counter.h>
#include <rex/system/interfaces/graphics.h>
#include <rex/system/xmemory.h>

#include "native_renderer/fh1_gpu_corpus.h"

REXCVAR_DEFINE_BOOL(pinyon_shift_fh1_clear_producer_trace, false, "Pinyon Shift",
                    "Record bounded guest clear-producer timing and shader copies")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_INT32(pinyon_shift_snr01_trace_source_frame, 0, "Pinyon Shift",
                     "Trace one source frame's procedural scopes and indexed PM4 headers")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_BOOL(pinyon_shift_snr01_trace_resident_packet_writers, false,
                    "Pinyon Shift", "Trace bounded resident PM4 packet writes")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_BOOL(pinyon_shift_snr01_watch_packet_pages, false,
                    "Pinyon Shift", "Watch observed PM4 packet pages for guest access")
    .lifecycle(rex::cvar::Lifecycle::kRequiresRestart);
REXCVAR_DEFINE_INT32(pinyon_shift_snr_m02_trace_source_frame, 0, "Pinyon Shift",
                     "Trace the title command-position wait for three frames")
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
  uint32_t camera = 0;
};
struct Snr01TrackCallScope {
  uint64_t ordinal;
  uint64_t view_call;
  uint64_t first_bucket;
};
struct Snr01TrackBucketScope {
  uint32_t presenter;
  uint32_t view;
  uint32_t bucket;
  uint32_t entry;
  uint32_t record;
  uint32_t secondary_record = 0;
  uint32_t remaining;
  uint64_t first_semantic_packet;
  uint64_t first_direct_packet;
  uint64_t ordinal;
  bool secondary_seen = false;
  uint32_t first_object = 0;
  uint32_t first_vtable = 0;
  int32_t first_guard = -1;
  uint32_t secondary_resolved = 0;
  bool secondary_resolved_seen = false;
  uint8_t secondary_byte52 = 0;
  uint8_t secondary_byte55 = 0;
  uint32_t auxiliary_record = 0;
  uint32_t auxiliary_resolved = 0;
  uint32_t auxiliary_flag = 0;
  bool auxiliary_seen = false;
  uint32_t second_dispatch_target = 0;
  uint32_t bound_context = 0;
  uint32_t bound_slot = 0;
  uint32_t bound_record = 0;
  uint32_t bound_target = 0;
  uint32_t bound_vertex_descriptor = 0;
  uint32_t bound_vertex_address = 0;
  uint32_t bound_vertex_size = 0;
  uint32_t vegetation_owner = 0;
  uint32_t vegetation_record_offset = 0;
  uint32_t vegetation_stream_offset = 0;
  uint32_t vegetation_record_base = 0;
  uint32_t vegetation_selected_record = 0;
  uint64_t track_call = 0;
};
struct Snr01SecondDrawScope {
  uint64_t bucket_entry;
  uint32_t target;
  uint32_t context;
  uint32_t arg4;
  uint32_t arg5;
  uint32_t arg6;
  uint32_t bound_context;
  uint32_t bound_slot;
  uint32_t bound_record;
  uint32_t bound_target;
  uint32_t bound_vertex_descriptor;
  uint32_t bound_vertex_address;
  uint32_t bound_vertex_size;
  uint32_t vegetation_owner;
  uint32_t vegetation_record_offset;
  uint32_t vegetation_stream_offset;
  uint32_t vegetation_record_base;
  uint32_t vegetation_selected_record;
  uint64_t first_semantic_packet;
  uint64_t first_direct_packet;
  uint64_t ordinal;
};
struct Snr01ItemNodeScope {
  uint32_t node;
  uint32_t list_head;
  uint32_t receiver;
  uint32_t index;
  uint32_t render_owner;
  uint64_t view_call;
  uint64_t bucket_entry;
  uint64_t first_item_call;
  uint64_t first_semantic_packet;
  uint64_t ordinal;
};
thread_local std::vector<Snr01EmitterScope> snr01_emitter_scopes;
std::atomic<rex::memory::Memory*> snr01_memory{nullptr};
thread_local std::vector<Snr01DirectScope> snr01_direct_scopes;
thread_local std::vector<uint32_t> snr01_indexed2_callers;
thread_local std::vector<Snr01ViewScope> snr01_view_scopes;
thread_local std::vector<Snr01TrackCallScope> snr01_track75_scopes;
thread_local std::vector<Snr01TrackBucketScope> snr01_track_bucket_scopes;
thread_local std::vector<Snr01SecondDrawScope> snr01_second_draw_scopes;
thread_local std::vector<Snr01ItemNodeScope> snr01_item_node_scopes;
thread_local std::vector<uint32_t> snr01_primary_indirect_callers;
thread_local std::vector<uint32_t> snr01_queued_indirect_callers;
struct Snr01WorkerScope {
  uint32_t stream;
  uint32_t queue;
  uint64_t first_packet;
};
thread_local std::vector<Snr01WorkerScope> snr01_worker_scopes;
thread_local std::vector<uint32_t> snr01_deferred_indirect_commands;
thread_local std::vector<uint32_t> snr01_inline_indirect_callers;
thread_local std::vector<uint32_t> snr01_command_refill_callers;
thread_local std::vector<uint32_t> snr01_render_request_callers;
struct Snr01RenderThreadRequest {
  uint64_t ordinal;
  uint32_t object;
  uint32_t mode;
  uint32_t request;
  uint64_t first_view;
};
thread_local std::vector<Snr01RenderThreadRequest> snr01_render_thread_requests;
thread_local uint64_t snr01_render_thread_request_count = 0;
thread_local uint64_t snr01_scene_indirect_count = 0;
thread_local std::vector<uint32_t> snr01_scene_indirect_callers;
struct Snr01SceneListFlush {
  uint32_t caller;
  uint32_t owner;
  uint32_t owner_first_word;
};
thread_local std::vector<Snr01SceneListFlush> snr01_scene_list_flushes;
std::atomic<uint32_t> snr01_vehicle_map_pool_root{0};
std::mutex snr01_player_mutex;
std::set<uint32_t> snr01_forza_players;
std::map<uint32_t, uint32_t> snr01_car_presentations;
thread_local std::set<uint32_t> snr01_view8_flush_owners;
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
thread_local uint64_t snr01_unmatched_track75_exits = 0;
thread_local uint64_t snr01_track79_count = 0;
thread_local uint64_t snr01_track_pass_count = 0;
thread_local uint64_t snr01_view_begin_count = 0;
thread_local uint64_t snr01_view_selected_count = 0;
thread_local uint64_t snr01_view_track_count = 0;
thread_local uint64_t snr01_camera_method_count = 0;
thread_local uint64_t snr01_indexed2_owner_count = 0;
thread_local uint64_t snr01_track_bucket_count = 0;
thread_local uint64_t snr01_second_draw_count = 0;
thread_local uint64_t snr01_second_draw_skips = 0;
thread_local uint64_t snr01_unmatched_second_draw_exits = 0;
thread_local uint64_t snr01_item_node_count = 0;
thread_local uint64_t snr01_direct_call_count = 0;
thread_local uint64_t snr01_direct_packet_count = 0;
thread_local uint64_t snr01_resident_packet_count = 0;
std::mutex snr01_watch_mutex;
std::set<uint32_t> snr01_watch_pages;
void* snr01_watch_access_handle = nullptr;
void* snr01_watch_invalidation_handle = nullptr;
std::atomic<uint32_t> snr01_watch_events{0};
constexpr uint32_t kSnr01WatchPageLimit = 1024;
constexpr uint32_t kSnr01WatchEventLimit = 8192;
thread_local uint64_t snr01_primary_indirect_packet_count = 0;
thread_local uint64_t snr01_unmatched_direct_exits = 0;
thread_local uint64_t snr01_unmatched_track_bucket_exits = 0;
thread_local uint64_t snr01_unmatched_item_node_exits = 0;
thread_local uint64_t snr01_unmatched_emitter_exits = 0;
thread_local uint64_t snr01_unmatched_dispatch_exits = 0;
thread_local uint64_t snr01_unmatched_render_state_exits = 0;
thread_local uint64_t snr01_unmatched_exits = 0;
constexpr uint64_t kSnr01PacketLimit = 8192;
constexpr uint64_t kSnr01ProceduralLimit = 4096;
constexpr uint64_t kSnrM02WaitLimit = 512;
constexpr uint64_t kSnrM02WriterLimit = 2048;

struct SnrM02WaitScope {
  uint64_t ordinal;
  uint32_t device;
  uint32_t requested;
  uint32_t caller;
  uint32_t published_before;
  uint32_t produced_before;
  uint32_t snapshot_published = 0;
  uint32_t snapshot_counter = 0;
  uint32_t snapshot_timebase = 0;
  uint32_t recovery_counter = 0;
  uint32_t recoveries = 0;
  bool entered_loop = false;
  int64_t begin_ns;
};
thread_local std::vector<SnrM02WaitScope> snr_m02_wait_scopes;
thread_local uint64_t snr_m02_wait_count = 0;
thread_local uint64_t snr_m02_writer_count = 0;

bool SnrM02TraceCurrentFrame() {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr_m02_trace_source_frame);
  const auto frame = rex::perf::GetTotalCounter(
      rex::perf::CounterId::kSourceFrameCount);
  return target > 0 && frame + 1 >= uint64_t(target) &&
         frame <= uint64_t(target) + 1;
}

int64_t SnrM02NowNs() {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
             ClearClock::now().time_since_epoch())
      .count();
}

uint32_t SnrM02ReadU32(uint32_t address) {
  const auto* memory = snr01_memory.load(std::memory_order_acquire);
  return memory && address
             ? rex::memory::load_and_swap<uint32_t>(memory->TranslateVirtual(address))
             : 0;
}

uint32_t SnrM02Physical(uint32_t address) {
  const auto* memory = snr01_memory.load(std::memory_order_acquire);
  return memory && address ? memory->GetPhysicalAddress(address) : UINT32_MAX;
}

void Snr01RecordWatchedPages(const char* path, uint32_t start, uint32_t length,
                            bool is_write) {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  const uint64_t frame = rex::perf::GetTotalCounter(
      rex::perf::CounterId::kSourceFrameCount);
  if (target <= 0 || frame + 1 < uint64_t(target) ||
      frame > uint64_t(target) + 1) {
    return;
  }
  std::lock_guard lock(snr01_watch_mutex);
  for (auto it = snr01_watch_pages.lower_bound(start);
       it != snr01_watch_pages.end() && uint64_t(*it) < uint64_t(start) + length;
       ++it) {
    const uint32_t ordinal = ++snr01_watch_events;
    if (ordinal > kSnr01WatchEventLimit) {
      if (ordinal == kSnr01WatchEventLimit + 1) {
        REXGPU_INFO("FH1 SNR01 watched page trace limit reached");
      }
      return;
    }
    REXGPU_INFO("FH1 SNR01 watched page {{\"frame\":{},\"path\":\"{}\","
                "\"page\":{},\"is_write\":{}}}",
                frame, path, *it, is_write);
  }
}

void Snr01WatchAccess(void*, uint32_t start, uint32_t length, bool is_write) {
  Snr01RecordWatchedPages("guest_access", start, length, is_write);
}

std::pair<uint32_t, uint32_t> Snr01WatchInvalidation(
    void*, uint32_t start, uint32_t length, bool exact_range) {
  Snr01RecordWatchedPages(exact_range ? "exact_invalidation" : "invalidation",
                          start, length, true);
  return {start, length};
}

void Snr01ArmPacketPage(uint32_t packet_physical) {
  auto* memory = snr01_memory.load(std::memory_order_acquire);
  if (!memory ||
      !((packet_physical >= 0x14000000 && packet_physical < 0x16000000) ||
        (packet_physical >= 0x17000000 && packet_physical < 0x18000000))) {
    return;
  }
  const uint32_t page_size = uint32_t(rex::memory::page_size());
  const uint32_t page = packet_physical & ~(page_size - 1);
  {
    std::lock_guard lock(snr01_watch_mutex);
    if (snr01_watch_pages.size() >= kSnr01WatchPageLimit ||
        !snr01_watch_pages.insert(page).second) {
      return;
    }
  }
  memory->EnablePhysicalMemoryAccessCallbacks(page, page_size, true, false,
                                               true);
  REXGPU_INFO("FH1 SNR01 watch armed {{\"frame\":{},\"page\":{}}}",
              rex::perf::GetTotalCounter(
                  rex::perf::CounterId::kSourceFrameCount),
              page);
}

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

bool Snr01TraceLinkedWriteFrame() {
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  const uint64_t frame = rex::perf::GetTotalCounter(
      rex::perf::CounterId::kSourceFrameCount);
  return target > 0 && frame + 12 >= uint64_t(target) &&
         frame <= uint64_t(target) + 1;
}

uint64_t Snr01CameraMatrixHash(uint32_t camera, uint32_t offset) {
  if (!camera) {
    return 0;
  }
  auto* memory = snr01_memory.load(std::memory_order_acquire);
  if (!memory) {
    return 0;
  }
  uint64_t hash = 14695981039346656037ull;
  for (uint32_t i = 0; i < 16; ++i) {
    hash ^= rex::memory::load_and_swap<uint32_t>(
        memory->TranslateVirtual(camera + offset + i * 4));
    hash *= 1099511628211ull;
  }
  return hash;
}

void RecordSnr01ResidentPacket(const char* path, uint32_t previous_word,
                               uint32_t header_word, uint32_t command_owner) {
  static const bool enabled = REXCVAR_GET(
      pinyon_shift_snr01_trace_resident_packet_writers);
  if (!enabled) {
    return;
  }
  const uint32_t physical = (previous_word + 4) & 0x1FFFFFFF;
  if (physical < 0x14000000 ||
      (physical >= 0x16000000 && physical < 0x17000000) ||
      physical >= 0x18000000 ||
      ++snr01_resident_packet_count > kSnr01PacketLimit) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 resident packet {{\"frame\":{},\"ordinal\":{},"
      "\"path\":\"{}\",\"header_physical\":{},"
      "\"header_word\":{},\"command_owner\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      snr01_resident_packet_count, path, physical, header_word, command_owner);
}

void RecordSnr01SemanticPacket(const char* path, uint32_t previous_word,
                               uint32_t header_word, uint32_t command_owner) {
  RecordSnr01ResidentPacket(path, previous_word, header_word, command_owner);
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
  RecordSnr01ResidentPacket(path, previous_word, header_word, command_owner);
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
      "\"direct_caller_lr\":{},\"indexed2_caller_lr\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, path, guest_address, guest_address & 0x1FFFFFFF,
      header_word, command_owner,
      snr01_direct_scopes.empty() ? 0 : snr01_direct_scopes.back().ordinal,
      snr01_direct_scopes.empty() ? 0 : snr01_direct_scopes.back().caller_lr,
      snr01_indexed2_callers.empty() ? 0 : snr01_indexed2_callers.back());
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
  uint32_t packet_bytes = 0;
  uint64_t packet_hash = 0;
  const uint32_t buffer_end_offset = observation.command_buffer_end_offset
                                         ? observation.command_buffer_end_offset
                                         : observation.command_buffer_bytes;
  if (const auto* memory = snr01_memory.load(std::memory_order_acquire);
      memory && buffer_end_offset <= observation.command_buffer_bytes &&
      observation.draw_packet_physical_address >=
          observation.command_buffer_physical_address) {
    const uint32_t packet_offset = observation.draw_packet_physical_address -
                                   observation.command_buffer_physical_address;
    if (packet_offset < buffer_end_offset) {
      packet_bytes = std::min<uint32_t>(buffer_end_offset - packet_offset, 32);
      packet_hash = 14695981039346656037ull;
      const uint8_t* packet = memory->TranslatePhysical(
          observation.draw_packet_physical_address);
      for (uint32_t i = 0; i < packet_bytes; ++i) {
        packet_hash = (packet_hash ^ packet[i]) * 1099511628211ull;
      }
    }
  }
  REXGPU_INFO(
      "FH1 SNR01 prepared draw {{\"frame\":{},\"ordinal\":{},"
      "\"indirect_execution\":{},\"indirect_parent\":{},"
      "\"dispatch_packet_physical\":{},"
      "\"packet_physical\":{},\"packet_bytes\":{},"
      "\"packet_hash\":{},\"command_buffer\":{},"
      "\"command_bytes\":{},\"draw_end_offset\":{},\"vertex_shader\":{},"
      "\"pixel_shader\":{},\"index_count\":{},"
      "\"index_buffer_type\":{},\"index_buffer_guest_base\":{},"
      "\"index_buffer_length\":{},\"guest_primitive_type\":{},"
      "\"vertex_fetch_count\":{},\"texture_fetch_count\":{},"
      "\"render_target_bits\":{},\"attachment_state\":{},"
      "\"surface_info\":{},\"color_info\":[{},{},{},{}],"
      "\"depth_info\":{}}}",
      observation.frame_sequence, logged_draws,
      observation.indirect_buffer_execution_id,
      observation.indirect_buffer_parent_execution_id,
      observation.indirect_dispatch_packet_physical_address,
      observation.draw_packet_physical_address,
      packet_bytes, packet_hash,
      observation.command_buffer_physical_address,
      observation.command_buffer_bytes,
      observation.command_buffer_end_offset, observation.vertex_shader_hash,
      observation.pixel_shader_hash, observation.index_count,
      observation.index_buffer_type, observation.index_buffer_guest_base,
      observation.index_buffer_length, observation.guest_primitive_type,
      observation.vertex_fetch_count, observation.texture_fetch_count,
      observation.bound_render_target_bits,
      observation.fh1_execution_key.attachment_state,
      observation.surface_info, observation.color_info[0],
      observation.color_info[1], observation.color_info[2],
      observation.color_info[3], observation.depth_info);
  if (REXCVAR_GET(pinyon_shift_snr01_watch_packet_pages) &&
      observation.frame_sequence + 1 == uint64_t(target) && packet_bytes) {
    Snr01ArmPacketPage(observation.draw_packet_physical_address);
  }
  if (observation.frame_sequence == uint64_t(target) ||
      observation.frame_sequence == uint64_t(target) + 1) {
    for (uint32_t i = 0; i < observation.texture_fetch_count; ++i) {
      const auto& fetch = observation.texture_fetches[i];
      REXGPU_INFO(
          "FH1 SNR01 prepared texture fetch {{\"frame\":{},"
          "\"draw\":{},\"packet_physical\":{},"
          "\"fetch_constant\":{},\"type\":{},"
          "\"base_address\":{},\"mip_address\":{},"
          "\"format\":{},\"dimension\":{},"
          "\"width\":{},\"height\":{},\"stack_depth\":{}}}",
          observation.frame_sequence, logged_draws,
          observation.draw_packet_physical_address, fetch.fetch_constant,
          fetch.type, fetch.base_address, fetch.mip_address, fetch.format,
          fetch.dimension, fetch.width, fetch.height, fetch.stack_depth);
    }
  }
  if (observation.frame_sequence == uint64_t(target) + 1) {
    for (uint32_t i = 0;
         i < observation.vertex_fetch_count &&
         i < observation.vertex_fetch_capacity; ++i) {
      const auto& fetch = observation.vertex_fetches[i];
      REXGPU_INFO(
          "FH1 SNR01 prepared vertex fetch {{\"frame\":{},"
          "\"draw\":{},\"packet_physical\":{},\"slot\":{},"
          "\"fetch_constant\":{},\"stride_words\":{},"
          "\"guest_base\":{},\"length\":{},\"type\":{},"
          "\"source_packet_0\":{},\"source_packet_1\":{},"
          "\"source_execution_0\":{},\"source_execution_1\":{}}}",
          observation.frame_sequence, logged_draws,
          observation.draw_packet_physical_address, i,
          fetch.fetch_constant, fetch.stride_words, fetch.guest_base,
          fetch.length, fetch.type, fetch.source_packet_physical_0,
          fetch.source_packet_physical_1, fetch.source_execution_0,
          fetch.source_execution_1);
    }
  }
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
  static const int32_t target = REXCVAR_GET(pinyon_shift_snr01_trace_source_frame);
  if (target <= 0 || observation.frame_sequence + 1 < uint64_t(target) ||
      observation.frame_sequence > uint64_t(target) + 1) {
    return;
  }
  static thread_local uint64_t logged_frame = 0;
  static thread_local uint64_t logged_copies = 0;
  if (logged_frame != observation.frame_sequence) {
    logged_frame = observation.frame_sequence;
    logged_copies = 0;
  }
  if (++logged_copies > kSnr01PacketLimit) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 copy {{\"frame\":{},\"ordinal\":{},"
      "\"copy_sequence\":{},\"attachment_state\":{},"
      "\"surface_info\":{},\"color_info\":[{},{},{},{}],"
      "\"depth_info\":{},\"copy_control\":{},"
      "\"source_base_tiles\":{},\"resolve_base_tiles\":{},"
      "\"resolve_width\":{},\"resolve_height\":{},"
      "\"dest_base\":{},\"dest_pitch\":{},"
      "\"written_address\":{},\"written_length\":{},"
      "\"succeeded\":{}}}",
      observation.frame_sequence, logged_copies, observation.copy_sequence,
      observation.fh1_execution_key.attachment_state,
      observation.surface_info, observation.color_info[0],
      observation.color_info[1], observation.color_info[2],
      observation.color_info[3], observation.depth_info,
      observation.rb_copy_control, observation.source_target_base_tiles,
      observation.resolve_source_base_tiles, observation.resolve_guest_width,
      observation.resolve_guest_height, observation.rb_copy_dest_base,
      observation.rb_copy_dest_pitch, observation.written_address,
      observation.written_length, observation.succeeded);
}

}  // namespace

void InstallGraphicsCensus(rex::system::IGraphicsSystem* graphics_system,
                           rex::memory::Memory* memory) {
  if (!graphics_system) {
    return;
  }
  snr01_memory.store(memory, std::memory_order_release);
  if (memory && REXCVAR_GET(pinyon_shift_snr01_watch_packet_pages) &&
      REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) > 0) {
    snr01_watch_events.store(0, std::memory_order_relaxed);
    snr01_watch_access_handle = memory->RegisterPhysicalMemoryAccessCallback(
        Snr01WatchAccess, nullptr);
    snr01_watch_invalidation_handle =
        memory->RegisterPhysicalMemoryInvalidationCallback(
            Snr01WatchInvalidation, nullptr);
    REXGPU_INFO("FH1 SNR01 packet page watch active page_limit={} event_limit={}",
                kSnr01WatchPageLimit, kSnr01WatchEventLimit);
  }
  if (REXCVAR_GET(pinyon_shift_snr01_trace_resident_packet_writers)) {
    REXGPU_INFO("FH1 SNR01 resident packet survey active "
                "range=[0x14000000,0x16000000)+[0x17000000,0x18000000) "
                "per_thread_limit={}",
                kSnr01PacketLimit);
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
  graphics_system->SetCopyObserver(
      enabled || REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) > 0
          ? &ObserveCopy
          : nullptr);
}

void UninstallGraphicsCensus(rex::system::IGraphicsSystem* graphics_system) {
  if (graphics_system) {
    graphics_system->SetPreparedDrawObserver(nullptr);
    graphics_system->SetIndirectBufferObserver(nullptr);
    graphics_system->SetCopyObserver(nullptr);
  }
  auto* memory = snr01_memory.exchange(nullptr, std::memory_order_acq_rel);
  if (memory && snr01_watch_access_handle) {
    memory->UnregisterPhysicalMemoryAccessCallback(snr01_watch_access_handle);
    memory->UnregisterPhysicalMemoryInvalidationCallback(
        snr01_watch_invalidation_handle);
    snr01_watch_access_handle = nullptr;
    snr01_watch_invalidation_handle = nullptr;
    std::lock_guard lock(snr01_watch_mutex);
    snr01_watch_pages.clear();
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
        "\"unfinished_track75_scopes\":{},"
        "\"unmatched_track75_exits\":{},"
        "\"track_pass_calls\":{},"
        "\"track_bucket_entries\":{},"
        "\"unfinished_track_bucket_scopes\":{},"
        "\"unmatched_track_bucket_exits\":{},"
        "\"second_draw_calls\":{},\"unfinished_second_draw_scopes\":{},"
        "\"unmatched_second_draw_exits\":{},"
        "\"second_draw_skips\":{},"
        "\"item_nodes\":{},\"unfinished_item_node_scopes\":{},"
        "\"unmatched_item_node_exits\":{},"
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
        snr01_track75_scopes.size(), snr01_unmatched_track75_exits,
        snr01_track_pass_count,
        snr01_track_bucket_count, snr01_track_bucket_scopes.size(),
        snr01_unmatched_track_bucket_exits,
        snr01_second_draw_count, snr01_second_draw_scopes.size(),
        snr01_unmatched_second_draw_exits,
        snr01_second_draw_skips,
        snr01_item_node_count, snr01_item_node_scopes.size(),
        snr01_unmatched_item_node_exits,
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
  snr01_track75_scopes.clear();
  snr01_track_bucket_scopes.clear();
  snr01_second_draw_scopes.clear();
  snr01_item_node_scopes.clear();
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
      snr01_unmatched_track75_exits =
      snr01_track79_count = snr01_track_pass_count =
      snr01_track_bucket_count = snr01_unmatched_track_bucket_exits =
      snr01_second_draw_count = snr01_unmatched_second_draw_exits =
      snr01_second_draw_skips =
      snr01_item_node_count = snr01_unmatched_item_node_exits =
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

void PinyonShiftObserveTitleCounterWaitBegin(PPCRegister& r12,
                                            PPCRegister& r3, PPCRegister& r4) {
  if (!SnrM02TraceCurrentFrame() && snr_m02_wait_scopes.empty()) {
    return;
  }
  const uint64_t ordinal = ++snr_m02_wait_count;
  const uint32_t device = r3.u32;
  const uint32_t published_ptr = SnrM02ReadU32(device + 11024);
  snr_m02_wait_scopes.push_back(
      {ordinal, device, r4.u32, r12.u32, SnrM02ReadU32(published_ptr),
       SnrM02ReadU32(device + 11036), 0, 0, 0, 0, 0, false, SnrM02NowNs()});
  if (ordinal == kSnrM02WaitLimit + 1) {
    REXGPU_INFO("FH1 SNRM02 wait trace limit reached on this title thread");
  }
}

void PinyonShiftObserveTitleCounterWaitSnapshot(PPCRegister& r1) {
  if (snr_m02_wait_scopes.empty()) {
    return;
  }
  auto& scope = snr_m02_wait_scopes.back();
  scope.entered_loop = true;
  scope.snapshot_published = SnrM02ReadU32(r1.u32 + 88);
  scope.snapshot_counter = SnrM02ReadU32(r1.u32 + 92);
  scope.snapshot_timebase = SnrM02ReadU32(r1.u32 + 100);
}

void PinyonShiftObserveTitleCounterRecovery(PPCRegister& r30) {
  if (!snr_m02_wait_scopes.empty()) {
    ++snr_m02_wait_scopes.back().recoveries;
    snr_m02_wait_scopes.back().recovery_counter = r30.u32;
  }
}

void PinyonShiftObserveTitleCounterWaitEnd() {
  if (snr_m02_wait_scopes.empty()) {
    return;
  }
  const auto scope = snr_m02_wait_scopes.back();
  snr_m02_wait_scopes.pop_back();
  if (scope.ordinal > kSnrM02WaitLimit) {
    return;
  }
  const uint32_t published_ptr = SnrM02ReadU32(scope.device + 11024);
  const int64_t end_ns = SnrM02NowNs();
  REXGPU_INFO(
      "FH1 SNRM02 wait {{\"frame\":{},\"ordinal\":{},"
      "\"caller_lr\":{},\"device\":{},\"requested\":{},"
      "\"published_ptr\":{},\"published_physical\":{},"
      "\"published_before\":{},"
      "\"published_after\":{},\"produced_before\":{},"
      "\"produced_after\":{},\"entered_loop\":{},"
      "\"snapshot_published\":{},\"snapshot_counter\":{},"
      "\"snapshot_timebase\":{},\"recovery_counter\":{},"
      "\"recoveries\":{},"
      "\"begin_ns\":{},\"end_ns\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      scope.ordinal, scope.caller, scope.device, scope.requested,
      published_ptr, SnrM02Physical(published_ptr), scope.published_before,
      SnrM02ReadU32(published_ptr),
      scope.produced_before, SnrM02ReadU32(scope.device + 11036),
      scope.entered_loop, scope.snapshot_published, scope.snapshot_counter,
      scope.snapshot_timebase, scope.recovery_counter, scope.recoveries,
      scope.begin_ns, end_ns);
}

void PinyonShiftObserveTitleCounterPublish(PPCRegister& r11,
                                           PPCRegister& r6) {
  if (!SnrM02TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr_m02_writer_count;
  if (ordinal > kSnrM02WriterLimit) {
    if (ordinal == kSnrM02WriterLimit + 1) {
      REXGPU_INFO("FH1 SNRM02 writer trace limit reached on this title thread");
    }
    return;
  }
  const uint32_t device = r11.u32;
  const uint32_t published_ptr = SnrM02ReadU32(device + 11024);
  const uint32_t flag = SnrM02ReadU32(device + 11068) >> 16 & 0xFF;
  const uint32_t disable_word = SnrM02ReadU32(device + 21940);
  REXGPU_INFO(
      "FH1 SNRM02 writer {{\"frame\":{},\"ordinal\":{},"
      "\"device\":{},\"published_ptr\":{},\"published\":{},"
      "\"produced_before\":{},\"disable_word\":{},"
      "\"publish_flag\":{},\"expected_title_store\":{},"
      "\"time_ns\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, device, published_ptr, SnrM02ReadU32(published_ptr), r6.u32,
      disable_word, flag, disable_word == 0 && (flag & 2), SnrM02NowNs());
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
  if (ordinal == 8) {
    snr01_view8_flush_owners.clear();
  }
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
        "\"view\":{},\"arg4\":{},\"camera\":{},"
        "\"matrix80_hash\":{},\"matrix144_hash\":{},"
        "\"first_semantic\":{},\"last_semantic\":{},"
        "\"first_direct\":{},\"last_direct\":{},"
        "\"first_primary\":{},\"last_primary\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.view, scope.argument, scope.camera,
        Snr01CameraMatrixHash(scope.camera, 80),
        Snr01CameraMatrixHash(scope.camera, 144),
        scope.first_semantic_packet + 1, snr01_semantic_packet_count,
        scope.first_direct_packet + 1, snr01_direct_packet_count,
        scope.first_primary_packet + 1,
        snr01_primary_indirect_packet_count);
  }
  if (scope.ordinal == 8) {
    const uint32_t root = snr01_vehicle_map_pool_root.load(
        std::memory_order_acquire);
    if (root) {
      REXGPU_INFO("FH1 SNR01 player map entity {{\"frame\":{},"
                  "\"pool\":{},\"entity\":{},\"vtable\":{},"
                  "\"vehicle_id\":{},\"context\":{},"
                  "\"link72\":{},\"link72_first_word\":{},"
                  "\"link76\":{},\"link76_first_word\":{},"
                  "\"link84\":{},\"link84_first_word\":{}}}",
                  rex::perf::GetTotalCounter(
                      rex::perf::CounterId::kSourceFrameCount),
                  root, root + 32, SnrM02ReadU32(root + 32),
                  SnrM02ReadU32(root + 44), SnrM02ReadU32(root + 16),
                  SnrM02ReadU32(root + 104),
                  SnrM02ReadU32(SnrM02ReadU32(root + 104)),
                  SnrM02ReadU32(root + 108),
                  SnrM02ReadU32(SnrM02ReadU32(root + 108)),
                  SnrM02ReadU32(root + 116),
                  SnrM02ReadU32(SnrM02ReadU32(root + 116)));
    }
    std::lock_guard lock(snr01_player_mutex);
    uint32_t local_car = 0;
    for (uint32_t player : snr01_forza_players) {
      if (SnrM02ReadU32(player) != 0x8201EB4C) {
        continue;
      }
      REXGPU_INFO("FH1 SNR01 Forza player {{\"frame\":{},\"player\":{},"
                  "\"vtable\":{},"
                  "\"link160\":{},\"link160_first_word\":{},"
                  "\"link164\":{},\"link164_first_word\":{},"
                  "\"link168\":{},\"link172\":{},\"link176\":{},"
                  "\"link180\":{},\"link180_first_word\":{}}}",
                  rex::perf::GetTotalCounter(
                      rex::perf::CounterId::kSourceFrameCount),
                  player, SnrM02ReadU32(player), SnrM02ReadU32(player + 160),
                  SnrM02ReadU32(SnrM02ReadU32(player + 160)),
                  SnrM02ReadU32(player + 164),
                  SnrM02ReadU32(SnrM02ReadU32(player + 164)),
                  SnrM02ReadU32(player + 168), SnrM02ReadU32(player + 172),
                  SnrM02ReadU32(player + 176), SnrM02ReadU32(player + 180),
                  SnrM02ReadU32(SnrM02ReadU32(player + 180)));
      if (SnrM02ReadU32(SnrM02ReadU32(player + 164)) == 0x82014510) {
        local_car = SnrM02ReadU32(player + 160);
      }
    }
    const uint32_t local_livery = local_car ? SnrM02ReadU32(local_car + 12292) : 0;
    for (const auto& [presentation, constructor_arg] :
         snr01_car_presentations) {
      if (SnrM02ReadU32(presentation) != 0x82003A54) {
        continue;
      }
      REXGPU_INFO(
          "FH1 SNR01 car presentation {{\"frame\":{},"
          "\"presentation\":{},\"constructor_arg\":{},"
          "\"constructor_arg_first_word\":{},\"view8_owner\":{}}}",
          rex::perf::GetTotalCounter(
              rex::perf::CounterId::kSourceFrameCount),
          presentation, constructor_arg, SnrM02ReadU32(constructor_arg),
          snr01_view8_flush_owners.contains(presentation));
      if (local_livery && SnrM02ReadU32(presentation + 2800) == local_livery) {
        REXGPU_INFO(
            "FH1 SNR01 local car presentation link "
            "{{\"frame\":{},\"car\":{},\"presentation\":{},"
            "\"livery\":{},\"livery_vtable\":{},\"view8_owner\":{}}}",
            rex::perf::GetTotalCounter(
                rex::perf::CounterId::kSourceFrameCount),
            local_car, presentation, local_livery, SnrM02ReadU32(local_livery),
            snr01_view8_flush_owners.contains(presentation));
      }
    }
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

void PinyonShiftObservePresentationViewObject400(
    PPCRegister& r31, PPCRegister& r3, PPCRegister& r11) {
  if (!Snr01TraceCurrentFrame() || snr01_view_scopes.empty()) {
    return;
  }
  const uint32_t camera = r11.u32 == 0x82002F64 ? r3.u32 : 0;
  snr01_view_scopes.back().camera = camera;
  REXGPU_INFO(
      "FH1 SNR01 view object400 {{\"frame\":{},\"call\":{},"
      "\"view\":{},\"object\":{},\"vtable\":{},"
      "\"matrix80_hash\":{},\"matrix144_hash\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      snr01_view_scopes.back().ordinal, r31.u32, r3.u32, r11.u32,
      Snr01CameraMatrixHash(camera, 80), Snr01CameraMatrixHash(camera, 144));
}

void ObserveSnr01CameraMethod(uint32_t slot, PPCRegister& r3,
                             PPCRegister& r4) {
  if (!Snr01TraceLinkedWriteFrame() || ++snr01_camera_method_count > 1024) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 camera method {{\"frame\":{},\"ordinal\":{},"
      "\"slot\":{},\"camera\":{},\"arg4\":{},"
      "\"view_call\":{},\"view\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      snr01_camera_method_count, slot, r3.u32, r4.u32,
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal,
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().view);
}

void PinyonShiftObserveCameraMethod11(PPCRegister& r3, PPCRegister& r4) {
  ObserveSnr01CameraMethod(11, r3, r4);
}

void PinyonShiftObserveCameraMethod12(PPCRegister& r3, PPCRegister& r4) {
  ObserveSnr01CameraMethod(12, r3, r4);
}

void PinyonShiftObserveCameraMethod43(PPCRegister& r3, PPCRegister& r4) {
  ObserveSnr01CameraMethod(43, r3, r4);
}

void PinyonShiftObserveCameraMethod44(PPCRegister& r3, PPCRegister& r4) {
  ObserveSnr01CameraMethod(44, r3, r4);
}

void PinyonShiftObservePresentationSelectedContextVtable(
    PPCRegister& r31, PPCRegister& r25, PPCRegister& r11) {
  if (!Snr01TraceCurrentFrame() || snr01_view_scopes.empty()) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 selected context vtable {{\"frame\":{},\"call\":{},"
      "\"view\":{},\"context\":{},\"vtable\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      snr01_view_scopes.back().ordinal, r31.u32, r25.u32, r11.u32);
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
  const uint64_t view_call = snr01_view_scopes.empty()
                                 ? 0
                                 : snr01_view_scopes.back().ordinal;
  snr01_track75_scopes.push_back(
      {ordinal, view_call, snr01_track_bucket_count});
  if (ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 track presentation {{\"frame\":{},\"slot\":75,"
        "\"call\":{},\"view_call\":{},\"caller_lr\":{},\"receiver\":{},"
        "\"arg4\":{},\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"arg8\":{},\"arg9\":{},\"arg10\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        ordinal, view_call, r12.u32, r3.u32, r4.u32, r5.u32, r6.u32,
        r7.u32, r8.u32, r9.u32, r10.u32);
  }
}

void PinyonShiftObserveTrackPresentation75End() {
  if (snr01_track75_scopes.empty()) {
    if (Snr01TraceCurrentFrame()) {
      ++snr01_unmatched_track75_exits;
    }
    return;
  }
  const auto scope = snr01_track75_scopes.back();
  snr01_track75_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 track presentation end {{\"frame\":{},"
        "\"call\":{},\"view_call\":{},"
        "\"first_bucket\":{},\"last_bucket\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.view_call, scope.first_bucket + 1,
        snr01_track_bucket_count);
  }
}

void PinyonShiftObserveTrackBucketEntryBegin(
    PPCRegister& r31, PPCRegister& r24, PPCRegister& r20, PPCRegister& r11,
    PPCRegister& r27, PPCRegister& r28, PPCRegister& r22) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  snr01_track_bucket_scopes.push_back(
      {r31.u32, r24.u32, r20.u32, r11.u32 + r27.u32, r28.u32,
       0, r22.u32, snr01_semantic_packet_count, snr01_direct_packet_count,
       ++snr01_track_bucket_count});
  snr01_track_bucket_scopes.back().track_call =
      snr01_track75_scopes.empty() ? 0 : snr01_track75_scopes.back().ordinal;
}

void PinyonShiftObserveTrackBucketSecondaryRecord(PPCRegister& r11,
                                                  PPCRegister& r28) {
  if (snr01_track_bucket_scopes.empty()) {
    return;
  }
  auto& scope = snr01_track_bucket_scopes.back();
  if (scope.entry == r11.u32) {
    scope.secondary_record = r28.u32;
    scope.secondary_seen = true;
  }
}

void PinyonShiftObserveTrackBucketFirstObject(PPCRegister& r3,
                                              PPCRegister& r11) {
  if (!snr01_track_bucket_scopes.empty()) {
    auto& scope = snr01_track_bucket_scopes.back();
    scope.first_object = r3.u32;
    scope.first_vtable = r11.u32;
  }
}

void PinyonShiftObserveTrackBucketFirstGuard(PPCRegister& r3) {
  if (!snr01_track_bucket_scopes.empty()) {
    snr01_track_bucket_scopes.back().first_guard = r3.u32 & 0xFF;
  }
}

void PinyonShiftObserveTrackBucketSecondaryResolved(PPCRegister& r3) {
  if (!snr01_track_bucket_scopes.empty()) {
    auto& scope = snr01_track_bucket_scopes.back();
    scope.secondary_resolved = r3.u32;
    scope.secondary_resolved_seen = true;
    if (r3.u32) {
      if (auto* memory = snr01_memory.load(std::memory_order_acquire)) {
        scope.secondary_byte52 = *memory->TranslateVirtual(r3.u32 + 52);
        scope.secondary_byte55 = *memory->TranslateVirtual(r3.u32 + 55);
      }
    }
  }
}

void PinyonShiftObserveTrackBucketAuxiliaryResolved(
    PPCRegister& r3, PPCRegister& r28, PPCRegister& r14) {
  if (!snr01_track_bucket_scopes.empty()) {
    auto& scope = snr01_track_bucket_scopes.back();
    scope.auxiliary_record = r28.u32;
    scope.auxiliary_resolved = r3.u32;
    scope.auxiliary_flag = r14.u32;
    scope.auxiliary_seen = true;
  }
}

void PinyonShiftObserveTrackBucketEntryEnd() {
  if (snr01_track_bucket_scopes.empty()) {
    if (Snr01TraceCurrentFrame()) {
      ++snr01_unmatched_track_bucket_exits;
    }
    return;
  }
  const auto scope = snr01_track_bucket_scopes.back();
  snr01_track_bucket_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 track bucket entry {{\"frame\":{},\"ordinal\":{},"
        "\"presenter\":{},\"view\":{},\"track_call\":{},\"bucket\":{},"
        "\"entry\":{},\"record\":{},\"secondary_record\":{},"
        "\"secondary_seen\":{},\"remaining\":{},"
        "\"first_object\":{},\"first_vtable\":{},"
        "\"first_guard\":{},\"secondary_resolved\":{},"
        "\"secondary_resolved_seen\":{},"
        "\"secondary_byte52\":{},\"secondary_byte55\":{},"
        "\"auxiliary_record\":{},\"auxiliary_resolved\":{},"
        "\"auxiliary_flag\":{},\"auxiliary_seen\":{},"
        "\"first_semantic\":{},\"last_semantic\":{},"
        "\"first_direct\":{},\"last_direct\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.presenter, scope.view, scope.track_call,
        scope.bucket,
        scope.entry, scope.record, scope.secondary_record,
        scope.secondary_seen, scope.remaining,
        scope.first_object, scope.first_vtable, scope.first_guard,
        scope.secondary_resolved, scope.secondary_resolved_seen,
        scope.secondary_byte52, scope.secondary_byte55,
        scope.auxiliary_record, scope.auxiliary_resolved,
        scope.auxiliary_flag, scope.auxiliary_seen,
        scope.first_semantic_packet + 1, snr01_semantic_packet_count,
        scope.first_direct_packet + 1, snr01_direct_packet_count);
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

void PinyonShiftObserveProceduralItemNodeBegin(
    PPCRegister& r30, PPCRegister& r24, PPCRegister& r3,
    PPCRegister& r11, PPCRegister& r25) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  snr01_item_node_scopes.push_back(
      {r30.u32, r24.u32, r3.u32, r11.u32, r25.u32,
       snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal,
       snr01_track_bucket_scopes.empty()
           ? 0 : snr01_track_bucket_scopes.back().ordinal,
       snr01_procedural_count, snr01_semantic_packet_count,
       ++snr01_item_node_count});
}

void PinyonShiftObserveProceduralItemNodeEnd() {
  if (snr01_item_node_scopes.empty()) {
    if (Snr01TraceCurrentFrame()) {
      ++snr01_unmatched_item_node_exits;
    }
    return;
  }
  const auto scope = snr01_item_node_scopes.back();
  snr01_item_node_scopes.pop_back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 item node {{\"frame\":{},\"ordinal\":{},"
        "\"node\":{},\"list_head\":{},\"receiver\":{},"
        "\"index\":{},\"render_owner\":{},\"view_call\":{},"
        "\"bucket_entry\":{},\"first_item\":{},\"last_item\":{},"
        "\"first_semantic\":{},\"last_semantic\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.node, scope.list_head, scope.receiver,
        scope.index, scope.render_owner, scope.view_call,
        scope.bucket_entry, scope.first_item_call + 1,
        snr01_procedural_count, scope.first_semantic_packet + 1,
        snr01_semantic_packet_count);
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

void PinyonShiftObserveProceduralResourceCandidate(
    PPCRegister& r4, PPCRegister& r5, PPCRegister& r6) {
  if (!Snr01TraceCurrentFrame() || snr01_procedural_scopes.empty()) {
    return;
  }
  const auto& scope = snr01_procedural_scopes.back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 resource candidate {{\"frame\":{},\"call\":{},"
        "\"descriptor\":{},\"key\":{},\"slot\":{},"
        "\"resolver_context\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.descriptor_address, r4.u32, r5.u32, r6.u32);
  }
}

void PinyonShiftObserveProceduralResourceResolution(PPCRegister& r3) {
  if (!Snr01TraceCurrentFrame() || snr01_procedural_scopes.empty()) {
    return;
  }
  const auto& scope = snr01_procedural_scopes.back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 resource resolution {{\"frame\":{},\"call\":{},"
        "\"object\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, r3.u32);
  }
}

void PinyonShiftObserveProceduralResourceBind(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r11) {
  if (!Snr01TraceCurrentFrame() || snr01_procedural_scopes.empty()) {
    return;
  }
  const auto& scope = snr01_procedural_scopes.back();
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 resource bind {{\"frame\":{},\"call\":{},"
        "\"context\":{},\"slot\":{},\"object\":{},"
        "\"target\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, r3.u32, r4.u32, r5.u32, r11.u32);
  }
}

void PinyonShiftObserveSecondTrackDispatch(
    PPCRegister& r31, PPCRegister& r11, PPCRegister& r4,
    PPCRegister& r5, PPCRegister& r6, PPCRegister& r7,
    PPCRegister& r8, PPCRegister& r9, PPCRegister& r10) {
  if (!Snr01TraceCurrentFrame() || snr01_track_bucket_scopes.empty()) {
    return;
  }
  auto& bucket = snr01_track_bucket_scopes.back();
  bucket.second_dispatch_target = r11.u32;
  if (bucket.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 second track dispatch {{\"frame\":{},"
        "\"bucket_entry\":{},\"object\":{},\"target\":{},"
        "\"arg4\":{},\"arg5\":{},\"arg6\":{},\"arg7\":{},"
        "\"arg8\":{},\"arg9\":{},\"arg10\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        bucket.ordinal, r31.u32, r11.u32, r4.u32, r5.u32,
        r6.u32, r7.u32, r8.u32, r9.u32, r10.u32);
  }
}

void PinyonShiftObserveSecondDrawBegin(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r5, PPCRegister& r6) {
  if (!Snr01TraceCurrentFrame() || snr01_track_bucket_scopes.empty()) {
    return;
  }
  const auto& bucket = snr01_track_bucket_scopes.back();
  snr01_second_draw_scopes.push_back(
      {bucket.ordinal, bucket.second_dispatch_target,
       r3.u32, r4.u32, r5.u32, r6.u32,
       bucket.bound_context, bucket.bound_slot, bucket.bound_record,
       bucket.bound_target, bucket.bound_vertex_descriptor,
       bucket.bound_vertex_address, bucket.bound_vertex_size,
       bucket.vegetation_owner, bucket.vegetation_record_offset,
       bucket.vegetation_stream_offset, bucket.vegetation_record_base,
       bucket.vegetation_selected_record,
       snr01_semantic_packet_count, snr01_direct_packet_count,
       ++snr01_second_draw_count});
}

void PinyonShiftObserveSecondStateBind(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
    PPCRegister& r11) {
  if (!Snr01TraceCurrentFrame() || snr01_track_bucket_scopes.empty()) {
    return;
  }
  auto& bucket = snr01_track_bucket_scopes.back();
  bucket.bound_context = r3.u32;
  bucket.bound_slot = r4.u32;
  bucket.bound_record = r5.u32;
  bucket.bound_target = r11.u32;
  bucket.bound_vertex_descriptor = 0;
  bucket.bound_vertex_address = 0;
  bucket.bound_vertex_size = 0;
  if (r11.u32 == 0x82415CA8 && r4.u32 == 0 && r5.u32) {
    if (auto* memory = snr01_memory.load(std::memory_order_acquire)) {
      auto read = [memory](uint32_t address) {
        return rex::memory::load_and_swap<uint32_t>(memory->TranslateVirtual(address));
      };
      bucket.bound_vertex_descriptor = read(r5.u32);
      if (bucket.bound_vertex_descriptor) {
        bucket.bound_vertex_address = read(bucket.bound_vertex_descriptor + 24);
        bucket.bound_vertex_size = read(bucket.bound_vertex_descriptor + 28);
      }
    }
  }
}

void PinyonShiftObserveVegetationStateBind(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r5, PPCRegister& r11,
    PPCRegister& r23, PPCRegister& r24, PPCRegister& r26, PPCRegister& r27) {
  PinyonShiftObserveSecondStateBind(r3, r4, r5, r11);
  if (!Snr01TraceCurrentFrame() || snr01_track_bucket_scopes.empty()) {
    return;
  }
  auto& bucket = snr01_track_bucket_scopes.back();
  bucket.vegetation_owner = r23.u32;
  bucket.vegetation_record_offset = r24.u32;
  bucket.vegetation_stream_offset = r26.u32;
  bucket.vegetation_selected_record = r27.u32;
  if (auto* memory = snr01_memory.load(std::memory_order_acquire)) {
    bucket.vegetation_record_base = rex::memory::load_and_swap<uint32_t>(
        memory->TranslateVirtual(r23.u32 + 108 + r26.u32));
  }
}

void PinyonShiftObserveSecondDrawEnd() {
  if (snr01_second_draw_scopes.empty()) {
    if (Snr01TraceCurrentFrame() && !snr01_track_bucket_scopes.empty()) {
      ++snr01_second_draw_skips;
    }
    return;
  }
  const auto scope = snr01_second_draw_scopes.back();
  snr01_second_draw_scopes.pop_back();
  if (snr01_track_bucket_scopes.empty() ||
      snr01_track_bucket_scopes.back().ordinal != scope.bucket_entry) {
    ++snr01_unmatched_second_draw_exits;
  }
  if (scope.ordinal <= kSnr01ProceduralLimit) {
    REXGPU_INFO(
        "FH1 SNR01 second draw call {{\"frame\":{},\"ordinal\":{},"
        "\"bucket_entry\":{},\"target\":{},\"context\":{},"
        "\"arg4\":{},\"arg5\":{},\"arg6\":{},"
        "\"bound_context\":{},\"bound_slot\":{},"
        "\"bound_record\":{},\"bound_target\":{},"
        "\"bound_vertex_descriptor\":{},\"bound_vertex_address\":{},"
        "\"bound_vertex_size\":{},"
        "\"vegetation_owner\":{},\"vegetation_record_offset\":{},"
        "\"vegetation_stream_offset\":{},\"vegetation_record_base\":{},"
        "\"vegetation_selected_record\":{},"
        "\"first_semantic\":{},\"last_semantic\":{},"
        "\"first_direct\":{},\"last_direct\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        scope.ordinal, scope.bucket_entry, scope.target,
        scope.context, scope.arg4, scope.arg5, scope.arg6,
        scope.bound_context, scope.bound_slot, scope.bound_record,
        scope.bound_target, scope.bound_vertex_descriptor,
        scope.bound_vertex_address, scope.bound_vertex_size,
        scope.vegetation_owner, scope.vegetation_record_offset,
        scope.vegetation_stream_offset, scope.vegetation_record_base,
        scope.vegetation_selected_record,
        scope.first_semantic_packet + 1, snr01_semantic_packet_count,
        scope.first_direct_packet + 1, snr01_direct_packet_count);
  }
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

void PinyonShiftObserveIndexed2Begin(PPCRegister& r12) {
  if (Snr01TraceCurrentFrame()) {
    snr01_indexed2_callers.push_back(r12.u32);
  }
}

void PinyonShiftObserveIndexed2End() {
  if (!snr01_indexed2_callers.empty()) {
    snr01_indexed2_callers.pop_back();
  }
}

void PinyonShiftObserveIndexed2Owner(PPCRegister& r12, PPCRegister& r3,
                                     PPCRegister& r4, PPCRegister& r5,
                                     PPCRegister& r7, PPCRegister& r8) {
  if (!Snr01TraceCurrentFrame() || r7.u32 != 4 ||
      ++snr01_indexed2_owner_count > 256) {
    return;
  }
  uint32_t receiver_word0 = 0;
  if (auto* memory = snr01_memory.load(std::memory_order_acquire)) {
    if (r3.u32) {
      receiver_word0 = rex::memory::load_and_swap<uint32_t>(
          memory->TranslateVirtual(r3.u32));
    }
  }
  REXGPU_INFO(
      "FH1 SNR01 indexed2 owner {{\"frame\":{},\"ordinal\":{},"
      "\"caller_lr\":{},\"receiver\":{},\"receiver_word0\":{},"
      "\"arg4\":{},\"arg5\":{},\"arg7\":{},\"arg8\":{},"
      "\"view_call\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      snr01_indexed2_owner_count, r12.u32, r3.u32, receiver_word0, r4.u32,
      r5.u32, r7.u32, r8.u32,
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal);
}

void PinyonShiftObserveQueuedIndirectBegin(
    PPCRegister& r12, PPCRegister&, PPCRegister&, PPCRegister&, PPCRegister&,
    PPCRegister&, PPCRegister&, PPCRegister&) {
  if (Snr01TraceLinkedWriteFrame()) {
    snr01_queued_indirect_callers.push_back(r12.u32);
  }
}

void PinyonShiftObserveQueuedIndirectEnd() {
  if (!snr01_queued_indirect_callers.empty()) {
    snr01_queued_indirect_callers.pop_back();
  }
}

void PinyonShiftObserveDeferredWorkerBegin(PPCRegister& r3,
                                           PPCRegister& r4) {
  if (!Snr01TracePrimaryIndirectFrame()) {
    return;
  }
  snr01_worker_scopes.push_back(
      {r3.u32, r4.u32, snr01_primary_indirect_packet_count});
  REXGPU_INFO(
      "FH1 SNR01 deferred worker begin {{\"frame\":{},"
      "\"stream\":{},\"queue\":{},\"first_packet\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      r3.u32, r4.u32, snr01_primary_indirect_packet_count + 1);
}

void PinyonShiftObserveDeferredWorkerEnd() {
  if (snr01_worker_scopes.empty()) {
    return;
  }
  const auto scope = snr01_worker_scopes.back();
  snr01_worker_scopes.pop_back();
  REXGPU_INFO(
      "FH1 SNR01 deferred worker end {{\"frame\":{},"
      "\"stream\":{},\"queue\":{},"
      "\"first_packet\":{},\"last_packet\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      scope.stream, scope.queue, scope.first_packet + 1,
      snr01_primary_indirect_packet_count);
}

void PinyonShiftObserveDeferredIndirectCommandBegin(PPCRegister& r31,
                                                    PPCRegister& r10,
                                                    PPCRegister& r11) {
  if (!Snr01TracePrimaryIndirectFrame()) {
    return;
  }
  snr01_deferred_indirect_commands.push_back(r31.u32);
  REXGPU_INFO(
      "FH1 SNR01 deferred indirect command {{\"frame\":{},"
      "\"command_guest\":{},\"command_physical\":{},"
      "\"opcode\":{},\"payload\":{},\"worker_stream\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      r31.u32, r31.u32 & 0x1FFFFFFF, r10.u32, r11.u32,
      snr01_worker_scopes.empty() ? 0 : snr01_worker_scopes.back().stream);
}

void PinyonShiftObserveDeferredIndirectCommandEnd() {
  if (!snr01_deferred_indirect_commands.empty()) {
    snr01_deferred_indirect_commands.pop_back();
  }
}

void PinyonShiftObserveLinkedIndirectWrite(
    PPCRegister& r29, PPCRegister& r11, PPCRegister& r30, PPCRegister& r27,
    PPCRegister& r25, PPCRegister& r31) {
  const uint64_t frame = rex::perf::GetTotalCounter(
      rex::perf::CounterId::kSourceFrameCount);
  if (!Snr01TraceLinkedWriteFrame()) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 linked indirect write {{\"frame\":{},\"block\":{},"
      "\"opcode_address\":{},\"opcode\":{},\"payload\":{},"
      "\"buffer\":{},\"device\":{},\"caller_lr\":{},"
      "\"view_call\":{},\"view\":{}}}",
      frame, r29.u32, r29.u32 + 4, r11.u32 | r30.u32, r27.u32,
      r25.u32, r31.u32,
      snr01_queued_indirect_callers.empty()
          ? 0
          : snr01_queued_indirect_callers.back(),
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal,
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().view);
}

void PinyonShiftObserveInlineIndirectBegin(PPCRegister& r12) {
  if (Snr01TraceLinkedWriteFrame()) {
    snr01_inline_indirect_callers.push_back(r12.u32);
  }
}

void PinyonShiftObserveCommandRefillBegin(PPCRegister& r12) {
  if (Snr01TraceCurrentFrame()) {
    snr01_command_refill_callers.push_back(r12.u32);
  }
}

void PinyonShiftObserveCommandRefillEnd() {
  if (!snr01_command_refill_callers.empty()) {
    snr01_command_refill_callers.pop_back();
  }
}

void PinyonShiftObserveRenderRequestBegin(PPCRegister& r12) {
  if (Snr01TraceCurrentFrame()) {
    snr01_render_request_callers.push_back(r12.u32);
  }
}

void PinyonShiftObserveRenderThreadRequestBegin(
    PPCRegister& r3, PPCRegister& r4, PPCRegister& r5) {
  if (!Snr01TraceCurrentFrame()) {
    return;
  }
  const uint64_t ordinal = ++snr01_render_thread_request_count;
  snr01_render_thread_requests.push_back(
      {ordinal, r3.u32, r4.u32, r5.u32, snr01_view_begin_count});
  REXGPU_INFO("FH1 SNR01 render thread request begin {{\"frame\":{},"
              "\"ordinal\":{},\"object\":{},\"mode\":{},"
              "\"request\":{},\"first_view\":{}}}",
              rex::perf::GetTotalCounter(
                  rex::perf::CounterId::kSourceFrameCount),
              ordinal, r3.u32, r4.u32, r5.u32, snr01_view_begin_count + 1);
}

void PinyonShiftObserveRenderThreadRequestEnd() {
  if (snr01_render_thread_requests.empty()) {
    return;
  }
  const auto request = snr01_render_thread_requests.back();
  snr01_render_thread_requests.pop_back();
  REXGPU_INFO("FH1 SNR01 render thread request end {{\"frame\":{},"
              "\"ordinal\":{},\"object\":{},\"mode\":{},"
              "\"request\":{},\"first_view\":{},\"last_view\":{}}}",
              rex::perf::GetTotalCounter(
                  rex::perf::CounterId::kSourceFrameCount),
              request.ordinal, request.object, request.mode, request.request,
              request.first_view + 1, snr01_view_begin_count);
}

void PinyonShiftObserveRenderRequestEnd() {
  if (!snr01_render_request_callers.empty()) {
    snr01_render_request_callers.pop_back();
  }
}

void PinyonShiftObserveInlineIndirectCachedWrite(
    PPCRegister& r3, PPCRegister& r9, PPCRegister& r11, PPCRegister& r31) {
  if (!Snr01TraceLinkedWriteFrame()) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 inline indirect write {{\"frame\":{},\"path\":0,"
      "\"command_guest\":{},\"command_physical\":{},"
      "\"opcode\":{},\"payload\":{},\"device\":{},"
      "\"caller_lr\":{},\"refill_caller_lr\":{},"
      "\"request_caller_lr\":{},"
      "\"view_call\":{},\"view\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      r3.u32, r3.u32 & 0x1FFFFFFF, r9.u32, r11.u32, r31.u32,
      snr01_inline_indirect_callers.empty()
          ? 0
          : snr01_inline_indirect_callers.back(),
      snr01_command_refill_callers.empty()
          ? 0
          : snr01_command_refill_callers.back(),
      snr01_render_request_callers.empty()
          ? 0
          : snr01_render_request_callers.back(),
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal,
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().view);
}

void PinyonShiftObserveInlineIndirectStreamWrite(
    PPCRegister& r11, PPCRegister& r30, PPCRegister& r29, PPCRegister& r31) {
  if (!Snr01TraceLinkedWriteFrame()) {
    return;
  }
  REXGPU_INFO(
      "FH1 SNR01 inline indirect write {{\"frame\":{},\"path\":1,"
      "\"command_guest\":{},\"command_physical\":{},"
      "\"opcode\":{},\"payload\":{},\"device\":{},"
      "\"caller_lr\":{},\"refill_caller_lr\":{},"
      "\"request_caller_lr\":{},"
      "\"view_call\":{},\"view\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      r11.u32, r11.u32 & 0x1FFFFFFF, r30.u32 | 0x81000000, r29.u32,
      r31.u32, snr01_inline_indirect_callers.empty()
                   ? 0
                   : snr01_inline_indirect_callers.back(),
      snr01_command_refill_callers.empty()
          ? 0
          : snr01_command_refill_callers.back(),
      snr01_render_request_callers.empty()
          ? 0
          : snr01_render_request_callers.back(),
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal,
      snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().view);
}

void PinyonShiftObserveInlineIndirectEnd() {
  if (!snr01_inline_indirect_callers.empty()) {
    snr01_inline_indirect_callers.pop_back();
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
      "\"caller_lr\":{},\"queued_caller_lr\":{},"
      "\"worker_stream\":{},\"worker_queue\":{},"
      "\"worker_command_physical\":{}}}",
      rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
      ordinal, guest_address & 0x1FFFFFFF, r10.u32, r31.u32, r27.u32,
      r24.u32, r25.u32, r26.u32, r29.u32, r21.u32,
      snr01_primary_indirect_callers.empty()
          ? 0
          : snr01_primary_indirect_callers.back(),
      snr01_queued_indirect_callers.empty()
          ? 0
          : snr01_queued_indirect_callers.back(),
      snr01_worker_scopes.empty() ? 0 : snr01_worker_scopes.back().stream,
      snr01_worker_scopes.empty() ? 0 : snr01_worker_scopes.back().queue,
      snr01_deferred_indirect_commands.empty()
          ? 0
          : snr01_deferred_indirect_commands.back() & 0x1FFFFFFF);
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

void PinyonShiftObserveSceneListFlushBegin(
    PPCRegister& r12, PPCRegister& r31, PPCRegister& r30) {
  if (Snr01TraceCurrentFrame()) {
    const uint32_t owner = r12.u32 == 0x8241A2A4 ? r30.u32 :
                           r12.u32 == 0x824399F0 ||
                                   r12.u32 == 0x8243CE0C ||
                                   r12.u32 == 0x824170BC
                               ? r31.u32
                               : 0;
    snr01_scene_list_flushes.push_back(
        {r12.u32, owner, owner ? SnrM02ReadU32(owner) : 0});
  }
}

void PinyonShiftObserveSceneListFlushEnd() {
  if (!snr01_scene_list_flushes.empty()) {
    snr01_scene_list_flushes.pop_back();
  }
}

void PinyonShiftObserveSnr01VehiclePoseOwner(PPCRegister& r30,
                                              PPCRegister& r31) {
  if (Snr01TraceCurrentFrame()) {
    REXGPU_INFO("FH1 SNR01 vehicle pose owner {{\"frame\":{},\"source\":{},"
                "\"owner\":{},\"owner_first_word\":{}}}",
                rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
                r30.u32, r31.u32, SnrM02ReadU32(r31.u32));
  }
}

void PinyonShiftObserveSnr01VehicleMapPoolInstalled(PPCRegister& r3,
                                                     PPCRegister& r31) {
  if (REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) <= 0) {
    return;
  }
  snr01_vehicle_map_pool_root.store(r3.u32, std::memory_order_release);
  REXGPU_INFO("FH1 SNR01 vehicle map pool {{\"frame\":{},"
              "\"installer\":{},\"pool\":{},\"player_entity\":{},"
              "\"player_vtable\":{},\"player_vehicle_id\":{}}}",
              rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
              r31.u32, r3.u32, r3.u32 ? r3.u32 + 32 : 0,
              r3.u32 ? SnrM02ReadU32(r3.u32 + 32) : 0,
              r3.u32 ? SnrM02ReadU32(r3.u32 + 44) : 0);
}

void PinyonShiftObserveSnr01VehicleIdAssigned(PPCRegister& r3,
                                               PPCRegister& r4) {
  const uint32_t root = snr01_vehicle_map_pool_root.load(
      std::memory_order_acquire);
  if (root && r3.u32 == root + 32) {
    REXGPU_INFO("FH1 SNR01 player vehicle ID assigned {{\"frame\":{},"
                "\"entity\":{},\"vehicle_id\":{}}}",
                rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
                r3.u32, r4.u32);
  }
}

void PinyonShiftObserveSnr01ForzaPlayerConstructed(PPCRegister& r3) {
  if (REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) > 0) {
    std::lock_guard lock(snr01_player_mutex);
    if (snr01_forza_players.size() < 32) {
      snr01_forza_players.insert(r3.u32);
    }
  }
}

void PinyonShiftObserveSnr01CarPresentationConstructed(PPCRegister& r3,
                                                       PPCRegister& r4) {
  if (REXCVAR_GET(pinyon_shift_snr01_trace_source_frame) > 0) {
    std::lock_guard lock(snr01_player_mutex);
    if (snr01_car_presentations.size() < 64) {
      snr01_car_presentations.emplace(r3.u32, r4.u32);
    }
  }
}

void PinyonShiftObserveSceneCommandBufferBegin(
    PPCRegister& r12, PPCRegister& r3, PPCRegister& r4, PPCRegister& r5) {
  if (Snr01TraceCurrentFrame()) {
    snr01_scene_indirect_callers.push_back(r12.u32);
    REXGPU_INFO("FH1 SNR01 scene indirect scope {{\"frame\":{},"
                "\"caller_lr\":{},\"device\":{},\"list_object\":{},"
                "\"arg5\":{},\"view_call\":{}}}",
                rex::perf::GetTotalCounter(
                    rex::perf::CounterId::kSourceFrameCount),
                r12.u32, r3.u32, r4.u32, r5.u32,
                snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal);
  }
}

void PinyonShiftObserveSceneCommandBufferEnd() {
  if (!snr01_scene_indirect_callers.empty()) {
    snr01_scene_indirect_callers.pop_back();
  }
}

void PinyonShiftObserveSceneCommandBuffer(PPCRegister& r24, PPCRegister& r10,
                                         PPCRegister& r11, PPCRegister& r30) {
  if (Snr01TraceCurrentFrame() &&
      ++snr01_scene_indirect_count <= kSnr01PacketLimit) {
    if (!snr01_view_scopes.empty() &&
        snr01_view_scopes.back().ordinal == 8 &&
        !snr01_scene_list_flushes.empty() &&
        snr01_scene_list_flushes.back().owner) {
      snr01_view8_flush_owners.insert(snr01_scene_list_flushes.back().owner);
    }
    REXGPU_INFO(
        "FH1 SNR01 scene indirect packet {{\"frame\":{},\"ordinal\":{},"
        "\"header_physical\":{},\"target_physical\":{},"
        "\"words\":{},\"list_object\":{},\"caller_lr\":{},"
        "\"flush_caller_lr\":{},\"flush_owner\":{},"
        "\"flush_owner_first_word\":{},"
        "\"view_call\":{},"
        "\"view\":{}}}",
        rex::perf::GetTotalCounter(rex::perf::CounterId::kSourceFrameCount),
        snr01_scene_indirect_count, r30.u32 & 0x1FFFFFFF,
        r10.u32 & 0x1FFFFFFF, r11.u32, r24.u32,
        snr01_scene_indirect_callers.empty()
            ? 0
            : snr01_scene_indirect_callers.back(),
        snr01_scene_list_flushes.empty()
            ? 0
            : snr01_scene_list_flushes.back().caller,
        snr01_scene_list_flushes.empty()
            ? 0
            : snr01_scene_list_flushes.back().owner,
        snr01_scene_list_flushes.empty()
            ? 0
            : snr01_scene_list_flushes.back().owner_first_word,
        snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().ordinal,
        snr01_view_scopes.empty() ? 0 : snr01_view_scopes.back().view);
  }
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
