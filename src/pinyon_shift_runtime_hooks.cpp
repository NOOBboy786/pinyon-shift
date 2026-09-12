#include <algorithm>
#include <atomic>
#include <array>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <mutex>
#include <string>
#include <string_view>

#include <fmt/format.h>
#include <rex/cvar.h>
#include <rex/memory.h>
#include <rex/ppc/context.h>
#include <rex/perf/counter.h>
#include <rex/system/kernel_state.h>
#include <rex/system/xmemory.h>

#include "pinyon_shift_diagnostics.h"
#include "fh1_render_test.h"
#include "native_renderer/graphics_hooks.h"
#include "ui/fh1_ui_api.h"

REXCVAR_DEFINE_BOOL(pinyon_shift_skip_opening_movies, false, "Pinyon Shift",
                    "Complete XMedia-backed movies immediately");
REXCVAR_DEFINE_BOOL(
    pinyon_shift_stabilize_vehicle_presentation, false, "Pinyon Shift",
    "Suppress isolated implausible player-vehicle presentation transforms");
REXCVAR_DEFINE_BOOL(disable_motion_blur, false, "Pinyon Shift",
                    "Disable Forza Horizon motion blur");
REXCVAR_DEFINE_BOOL(disable_depth_of_field, false, "Pinyon Shift",
                    "Disable Forza Horizon depth of field");

namespace {

std::atomic<uint32_t> g_cleanup_pointer_field{};
std::atomic<uint32_t> g_geometry_zero_index_buffer{};
std::atomic<uint64_t> g_last_frame_telemetry_ms{};
std::atomic<uint32_t> g_ui_component_trace_count{};
std::atomic<uint32_t> g_ui_list_trace_count{};
std::atomic<uint32_t> g_ui_pause_button_trace_count{};
std::atomic<uint32_t> g_ui_pause_menu_field_trace_count{};
std::atomic<uint32_t> g_ui_menu_field_trace_count{};
std::atomic<uint32_t> g_ui_menu_dispatch_trace_count{};
std::atomic<uint32_t> g_ui_text_value_trace_count{};
std::atomic<uint32_t> g_ui_pause_button_text_get_trace_count{};
std::atomic<uint32_t> g_ui_pause_button_count{};
std::array<uint32_t, 128> g_ui_pause_buttons{};
pinyon_shift::ui::Api g_ui_experiment_api(4u);
pinyon_shift::ui::SceneHandle g_ui_experiment_scene;
uint64_t g_ui_experiment_generation = 0;
uint32_t g_ui_experiment_button = 0;
bool g_ui_experiment_applied = false;
constexpr uint32_t kUiExperimentTextTargets = 16u;
// Label-scan window: the observed UI allocations span the 0x2E... and 0x40...
// regions, so the window covers both. Each frame scans a bounded slice.
constexpr uint32_t kUiLabelScanBegin = 0x2C000000u;
constexpr uint32_t kUiLabelScanEnd = 0x52000000u;
constexpr uint32_t kUiLabelScanBlockSize = 0x10000u;
constexpr uint32_t kUiLabelScanBytesPerFrame = 8u * 1024u * 1024u;
constexpr uint32_t kUiLabelMaximumWrites = 64u;
constexpr uint32_t kUiLabelRescanIntervalFrames = 45u;
constexpr std::string_view kUiExperimentRequestedLabel = "Pinyon UI";
std::array<uint32_t, kUiExperimentTextTargets> g_ui_experiment_buttons{};
std::atomic<uint32_t> g_ui_experiment_buttons_count{};
std::atomic<bool> g_ui_experiment_buttons_queued{};
std::atomic<uint64_t> g_last_vehicle_pose_ms{};
std::atomic<uint64_t> g_last_vehicle_discontinuity_ms{};
std::atomic<uint32_t> g_title_generation{1};
std::atomic<bool> g_cleanup_pointer_live{};
std::atomic<bool> g_opening_movie_skip_logged{};
std::mutex g_vehicle_hook_sample_mutex;
std::mutex g_save_snapshot_mutex;
std::mutex g_geometry_zero_index_buffer_mutex;

struct VehiclePose {
  float x = 0.0f;
  float y = 0.0f;
  float z = 0.0f;
  float w = 1.0f;
  float forward_x = 0.0f;
  float forward_y = 0.0f;
  float forward_z = 1.0f;
  float forward_w = 0.0f;
};

struct VehiclePresentationState {
  bool valid = false;
  uint32_t generation = 0;
  uint32_t source = 0;
  VehiclePose accepted;
  bool pending = false;
  VehiclePose pending_last;
  uint64_t pending_since_ms = 0;
};

VehiclePresentationState g_vehicle_presentation_state;

std::string Hex32(uint32_t value) { return fmt::format("{:08X}", value); }

uint32_t LoadGuestU32(uint32_t address) {
  auto* kernel_state = rex::system::kernel_state();
  auto* base = kernel_state->memory()->virtual_membase();
  return static_cast<uint32_t>(
      *rex::memory::GuestPtr<rex::be_u32*>(base, address));
}

uint8_t LoadGuestU8(uint32_t address) {
  auto* kernel_state = rex::system::kernel_state();
  auto* base = kernel_state->memory()->virtual_membase();
  return *rex::memory::GuestPtr<uint8_t*>(base, address);
}

float LoadGuestF32(uint32_t address) {
  return std::bit_cast<float>(LoadGuestU32(address));
}

void StoreGuestU32(uint32_t address, uint32_t value) {
  auto* kernel_state = rex::system::kernel_state();
  auto* base = kernel_state->memory()->virtual_membase();
  *rex::memory::GuestPtr<rex::be_u32*>(base, address) = value;
}

void StoreGuestU8(uint32_t address, uint8_t value) {
  auto* kernel_state = rex::system::kernel_state();
  auto* base = kernel_state->memory()->virtual_membase();
  *rex::memory::GuestPtr<uint8_t*>(base, address) = value;
}

void StoreGuestF32(uint32_t address, float value) {
  StoreGuestU32(address, std::bit_cast<uint32_t>(value));
}

float PositionDistanceSquared(const VehiclePose& lhs, const VehiclePose& rhs) {
  const float dx = lhs.x - rhs.x;
  const float dy = lhs.y - rhs.y;
  const float dz = lhs.z - rhs.z;
  return dx * dx + dy * dy + dz * dz;
}

bool IsPlausibleVehiclePose(const VehiclePose& pose) {
  const float forward_length_sq =
      pose.forward_x * pose.forward_x + pose.forward_y * pose.forward_y +
      pose.forward_z * pose.forward_z;
  return std::isfinite(pose.x) && std::isfinite(pose.y) &&
         std::isfinite(pose.z) && std::isfinite(pose.w) &&
         std::isfinite(forward_length_sq) &&
         std::abs(pose.x) <= 10000000.0f &&
         std::abs(pose.y) <= 10000000.0f &&
         std::abs(pose.z) <= 10000000.0f && std::abs(pose.w - 1.0f) <= 0.01f &&
         forward_length_sq >= 0.81f && forward_length_sq <= 1.21f;
}

void StoreVehiclePose(uint32_t position_address, uint32_t forward_address,
                      const VehiclePose& pose) {
  StoreGuestF32(position_address, pose.x);
  StoreGuestF32(position_address + 4, pose.y);
  StoreGuestF32(position_address + 8, pose.z);
  StoreGuestF32(position_address + 12, pose.w);
  StoreGuestF32(forward_address, pose.forward_x);
  StoreGuestF32(forward_address + 4, pose.forward_y);
  StoreGuestF32(forward_address + 8, pose.forward_z);
  StoreGuestF32(forward_address + 12, pose.forward_w);
}

bool FrameTelemetryEnabled() {
  static const bool enabled = [] {
#if defined(_WIN32)
    char* value = nullptr;
    size_t value_size = 0;
    if (_dupenv_s(&value, &value_size, "PINYON_SHIFT_M4_TELEMETRY") != 0) {
      return false;
    }
    const bool result = value && std::string_view(value) == "1";
    std::free(value);
    return result;
#else
    const char* value = std::getenv("PINYON_SHIFT_M4_TELEMETRY");
    return value && std::string_view(value) == "1";
#endif
  }();
  return enabled;
}

bool SaveTraceEnabled() {
  static const bool enabled = [] {
#if defined(_WIN32)
    char* value = nullptr;
    size_t value_size = 0;
    if (_dupenv_s(&value, &value_size, "PINYON_SHIFT_M5_SAVE_TRACE") != 0) {
      return false;
    }
    const bool result = value && std::string_view(value) == "1";
    std::free(value);
    return result;
#else
    const char* value = std::getenv("PINYON_SHIFT_M5_SAVE_TRACE");
    return value && std::string_view(value) == "1";
#endif
  }();
  return enabled;
}

bool UiTraceEnabled() {
  static const bool enabled = [] {
#if defined(_WIN32)
    char* value = nullptr;
    size_t value_size = 0;
    if (_dupenv_s(&value, &value_size, "PINYON_SHIFT_UI_TRACE") != 0) {
      return false;
    }
    const bool result = value && std::string_view(value) == "1";
    std::free(value);
    return result;
#else
    const char* value = std::getenv("PINYON_SHIFT_UI_TRACE");
    return value && std::string_view(value) == "1";
#endif
  }();
  return enabled;
}

// Default-off UI experiments. `hide_first` keeps the earlier +160 state-byte
// probe; `text_probe` samples the two embedded 12-byte CUI4TextElement objects
// of every observed pause button at a bounded cadence and records their
// {+4, +8} pair plus any readable string those words point to. It writes no
// guest state.
enum class UiExperimentMode {
  kNone,
  kHideFirst,
  kTextProbe,
  kLabelScan,
  kLabelWrite,
};

UiExperimentMode ComputeUiExperimentMode() {
  std::string_view requested;
#if defined(_WIN32)
  char* value = nullptr;
  size_t value_size = 0;
  if (_dupenv_s(&value, &value_size, "PINYON_SHIFT_UI_EXPERIMENT") != 0) {
    return UiExperimentMode::kNone;
  }
  const std::string owned = value ? std::string(value) : std::string();
  std::free(value);
  requested = owned;
#else
  const char* value = std::getenv("PINYON_SHIFT_UI_EXPERIMENT");
  requested = value ? std::string_view(value) : std::string_view();
#endif
  if (requested == "hide_first") {
    return UiExperimentMode::kHideFirst;
  }
  if (requested == "text_probe") {
    return UiExperimentMode::kTextProbe;
  }
  if (requested == "label_scan") {
    return UiExperimentMode::kLabelScan;
  }
  if (requested == "label_write") {
    return UiExperimentMode::kLabelWrite;
  }
  return UiExperimentMode::kNone;
}

// Replacement literal for the label write mode. Same-length overwrite of the
// located string, so no allocation or length field is touched.
std::string_view UiLabelWriteLiteral() {
  static const std::string value = [] {
#if defined(_WIN32)
    char* raw = nullptr;
    size_t size = 0;
    if (_dupenv_s(&raw, &size, "PINYON_SHIFT_UI_LABEL_WRITE") != 0) {
      return std::string("PINYONSHIFT");
    }
    const std::string owned =
        raw && raw[0] != '\0' ? std::string(raw) : std::string("PINYONSHIFT");
    std::free(raw);
    return owned;
#else
    const char* raw = std::getenv("PINYON_SHIFT_UI_LABEL_WRITE");
    return raw && raw[0] != '\0' ? std::string(raw) : std::string("PINYONSHIFT");
#endif
  }();
  return value;
}

// Optional literal for the label scan, so the probe is not tied to one screen.
std::string_view UiLabelScanLiteral() {
  static const std::string value = [] {
#if defined(_WIN32)
    char* raw = nullptr;
    size_t size = 0;
    if (_dupenv_s(&raw, &size, "PINYON_SHIFT_UI_LABEL_SCAN") != 0) {
      return std::string("MULTIPLAYER");
    }
    const std::string owned = raw && raw[0] != '\0' ? std::string(raw)
                                                    : std::string("MULTIPLAYER");
    std::free(raw);
    return owned;
#else
    const char* raw = std::getenv("PINYON_SHIFT_UI_LABEL_SCAN");
    return raw && raw[0] != '\0' ? std::string(raw) : std::string("MULTIPLAYER");
#endif
  }();
  return value;
}

UiExperimentMode UiExperimentModeValue() {
  static const UiExperimentMode mode = ComputeUiExperimentMode();
  return mode;
}

uint32_t CareerCheckpointSeedStage() {
  static const uint32_t stage = [] {
#if defined(_WIN32)
    char* value = nullptr;
    size_t value_size = 0;
    if (_dupenv_s(&value, &value_size,
                  "PINYON_SHIFT_M5_TEST_CAREER_CHECKPOINT") != 0) {
      return 0u;
    }
    const std::string_view requested = value ? std::string_view(value)
                                             : std::string_view();
    const uint32_t result =
        requested == "2"  ? 2u
        : requested == "3" ? 3u
        : requested == "7" ? 7u
        : requested == "10" ? 10u
                              : 0u;
    std::free(value);
    return result;
#else
    const char* value =
        std::getenv("PINYON_SHIFT_M5_TEST_CAREER_CHECKPOINT");
    const std::string_view requested = value ? std::string_view(value)
                                             : std::string_view();
    return requested == "2"  ? 2u
           : requested == "3" ? 3u
           : requested == "7" ? 7u
           : requested == "10" ? 10u
                                 : 0u;
#endif
  }();
  return stage;
}

uint64_t HashGuestBytes(uint32_t address, uint32_t size) {
  auto* kernel_state = rex::system::kernel_state();
  auto* base = kernel_state->memory()->virtual_membase();
  const auto* bytes = reinterpret_cast<const uint8_t*>(base) + address;
  uint64_t hash = 1469598103934665603ull;
  for (uint32_t i = 0; i < size; ++i) {
    hash ^= bytes[i];
    hash *= 1099511628211ull;
  }
  return hash;
}

void SnapshotSavePayload(std::string_view kind, uint32_t address, uint32_t size,
                         uint32_t caller_lr) {
  // These are the two known plaintext secure-save payload sizes. Limiting the
  // hook to them keeps diagnostics narrow and avoids copying unrelated stream
  // traffic through this generic title writer.
  if (!SaveTraceEnabled() || address == 0 ||
      (size != 19472 && size != 2928)) {
    return;
  }

  const uint64_t hash = HashGuestBytes(address, size);
  // The title mirrors its first-time-career state at this fixed address while
  // the onboarding state machine is alive. Recording it beside the serialized
  // body lets us distinguish a failed save from an intentionally deferred
  // onboarding checkpoint without changing either state.
  constexpr uint32_t kFirstTimeCareerStageAddress = 0x833067E0u;
  const uint32_t first_time_career_stage =
      LoadGuestU32(kFirstTimeCareerStageAddress);
  const auto directory =
      pinyon_shift::diagnostics::StateRoot() / "logs" / "save-snapshots";
  const auto filename =
      fmt::format("payload-{}-{}-{:016X}.bin", kind, size, hash);
  const auto path = directory / filename;
  bool created = false;
  {
    std::scoped_lock lock(g_save_snapshot_mutex);
    std::error_code error;
    std::filesystem::create_directories(directory, error);
    if (!error && !std::filesystem::exists(path, error)) {
      auto* kernel_state = rex::system::kernel_state();
      auto* base = kernel_state->memory()->virtual_membase();
      const auto* bytes = reinterpret_cast<const char*>(base) + address;
      std::ofstream stream(path, std::ios::binary | std::ios::trunc);
      if (stream) {
        stream.write(bytes, size);
        created = stream.good();
      }
    }
  }
  pinyon_shift::diagnostics::RecordEvent(
      "save.payload.snapshot",
      {{"address", Hex32(address)},
       {"size", fmt::format("{}", size)},
       {"kind", std::string(kind)},
       {"caller_lr", Hex32(caller_lr)},
       {"first_time_career_stage",
        fmt::format("{}", first_time_career_stage)},
       {"hash", fmt::format("{:016X}", hash)},
       {"snapshot", path.string()},
       {"created", created ? "1" : "0"}});
}

void SeedCareerCheckpointInSavePayload(uint32_t address, uint32_t size) {
  const uint32_t requested_stage = CareerCheckpointSeedStage();
  if (requested_stage == 0 || address == 0 || size != 19472) {
    return;
  }

  auto* kernel_state = rex::system::kernel_state();
  auto* base = kernel_state->memory()->virtual_membase();
  auto* bytes = reinterpret_cast<uint8_t*>(base) + address;
  constexpr std::string_view kActivityKey = "first_time_career_activity";
  const std::string_view body(reinterpret_cast<const char*>(bytes), size);
  const size_t key_offset = body.find(kActivityKey);
  if (key_offset == std::string_view::npos || key_offset + 64u > size ||
      bytes[key_offset + 29u] != 0x15u ||
      body.substr(key_offset + 30u, 21u) != "CFirstTimeCareerState" ||
      bytes[key_offset + 54u] != 0x01u ||
      bytes[key_offset + 58u] != 0x05u) {
    pinyon_shift::diagnostics::RecordEvent(
        "save.career_checkpoint.payload_seed", {{"result", "layout_mismatch"}});
    return;
  }

  const uint32_t value_address =
      address + static_cast<uint32_t>(key_offset) + 59u;
  // CFirstTimeCareerState serializes its byte-at-40 active flag first, then
  // its big-endian uint32 stage-at-44: [active][stage].
  const uint8_t previous_active = LoadGuestU8(value_address);
  const uint32_t previous_stage = LoadGuestU32(value_address + 1u);
  bytes[key_offset + 59u] = 1u;
  StoreGuestU32(value_address + 1u, requested_stage);
  pinyon_shift::diagnostics::RecordEvent(
      "save.career_checkpoint.payload_seed",
      {{"result", "seeded"},
       {"offset", fmt::format("{}", key_offset + 59u)},
       {"previous_stage", fmt::format("{}", previous_stage)},
       {"previous_active", fmt::format("{}", previous_active)},
       {"stage", fmt::format("{}", requested_stage)},
       {"active", "1"}});
}

bool OpeningMovieSkipRequested() {
  if (REXCVAR_GET(pinyon_shift_skip_opening_movies)) {
    return true;
  }
#if defined(_WIN32)
  char* value = nullptr;
  size_t value_size = 0;
  if (_dupenv_s(&value, &value_size, "PINYON_SHIFT_SKIP_OPENING_MOVIES") != 0) {
    return false;
  }
  const bool result = value && std::string_view(value) == "1";
  std::free(value);
  return result;
#else
  const char* value = std::getenv("PINYON_SHIFT_SKIP_OPENING_MOVIES");
  return value && std::string_view(value) == "1";
#endif
}

}  // namespace

static bool PinyonShiftGuestRangeReadable(uint32_t address, uint32_t size);
static std::string PinyonShiftReadGuestAscii(uint32_t address,
                                             uint32_t maximum_length);

bool PinyonShiftDisableMotionBlur() {
  return REXCVAR_GET(disable_motion_blur);
}

bool PinyonShiftDisableDepthOfField(PPCRegister& r11) {
  if (!REXCVAR_GET(disable_depth_of_field)) {
    return false;
  }
  r11.u64 = 0;
  return true;
}

void PinyonShiftCompleteOpeningMovie(PPCRegister& r3, PPCRegister& r30,
                                     PPCRegister& r31) {
  const uint32_t original_result = r3.u32;
  const bool skip = OpeningMovieSkipRequested();
  if (skip) {
    // This is the XMedia facade's normal end-of-stream result. Returning it
    // through the title's own wrapper runs the ordinary movie-finished event
    // path instead of bypassing profile/setup state.
    r3.u32 = 0x16660026u;
  }
  if (skip && !g_opening_movie_skip_logged.exchange(true, std::memory_order_acq_rel)) {
    pinyon_shift::diagnostics::RecordEvent(
        "opening_movie.skipped",
        {{"address", "82E5D8AC"},
         {"original_result", Hex32(original_result)},
         {"result", Hex32(r3.u32)},
         {"argument", Hex32(r30.u32)},
         {"object", Hex32(r31.u32)}});
  }
}

void PinyonShiftTraceUiSceneRegistry(PPCRegister& r3, PPCRegister& r24,
                                     PPCRegister& r30) {
  if (!UiTraceEnabled()) {
    return;
  }

  pinyon_shift::diagnostics::RecordEvent(
      "ui.scene_registry.constructed",
      {{"address", "824850A4"},
       {"object", Hex32(r3.u32)},
       {"context", Hex32(r24.u32)},
       {"owner", Hex32(r30.u32)}});

  constexpr uint32_t kRegistrySize = 2820u;
  if (!PinyonShiftGuestRangeReadable(r3.u32, kRegistrySize)) {
    return;
  }
  std::array<std::string, 192> seen{};
  size_t seen_count = 0;
  for (uint32_t offset = 0;
       offset + 4u <= kRegistrySize && seen_count < seen.size(); offset += 4u) {
    const uint32_t pointer = LoadGuestU32(r3.u32 + offset);
    if (pointer < 0x82000000u || pointer >= 0x83000000u) {
      continue;
    }
    const std::string name = PinyonShiftReadGuestAscii(pointer, 64u);
    if (name.empty() ||
        std::find(seen.begin(), seen.begin() + seen_count, name) !=
            seen.begin() + seen_count) {
      continue;
    }
    seen[seen_count++] = name;
    pinyon_shift::diagnostics::RecordEvent(
        "ui.scene_registry.name",
        {{"address", "824850A4"},
         {"object", Hex32(r3.u32)},
         {"offset", Hex32(offset)},
         {"value", Hex32(pointer)},
         {"name", name}});
  }
}

namespace {

void TraceUiDispatch(std::string_view kind, std::string_view address,
                     PPCRegister& object, PPCRegister& argument,
                     PPCRegister& target, PPCRegister* result = nullptr,
                     PPCRegister* vtable = nullptr) {
  if (!UiTraceEnabled()) {
    return;
  }
  const std::string event =
      std::string("ui.dispatch.") + std::string(kind);
  if (result != nullptr && vtable != nullptr) {
    pinyon_shift::diagnostics::RecordEvent(
        event,
        {{"address", address},
         {"object", Hex32(object.u32)},
         {"argument", Hex32(argument.u32)},
         {"target", Hex32(target.u32)},
         {"result", Hex32(result->u32)},
         {"vtable", Hex32(vtable->u32)}});
  } else {
    pinyon_shift::diagnostics::RecordEvent(
        event,
        {{"address", address},
         {"object", Hex32(object.u32)},
         {"argument", Hex32(argument.u32)},
         {"target", Hex32(target.u32)}});
  }
}

}  // namespace

void PinyonShiftTraceUiRegistryDispatch(PPCRegister& r3, PPCRegister& r4,
                                        PPCRegister& r11) {
  TraceUiDispatch("registry", "824850CC", r3, r4, r11);
}

void PinyonShiftTraceUiResourceDispatch(PPCRegister& r3, PPCRegister& r4,
                                        PPCRegister& r11) {
  TraceUiDispatch("resource", "824850E8", r3, r4, r11);
}

void PinyonShiftTraceUiSceneDispatch(PPCRegister& r3, PPCRegister& r4,
                                     PPCRegister& r11, PPCRegister& r31,
                                     PPCRegister& r30) {
  TraceUiDispatch("scene", "82485110", r3, r4, r11, &r3, &r30);
  if (!UiTraceEnabled() || !PinyonShiftGuestRangeReadable(r4.u32, 4u)) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "ui.dispatch.scene_argument",
      {{"address", "82485110"},
       {"argument_word0", Hex32(LoadGuestU32(r4.u32))},
       {"owner", Hex32(r31.u32)}});
}

void PinyonShiftTraceUiManagerEvent(PPCRegister& r3, PPCRegister& r4,
                                    PPCRegister& r11) {
  TraceUiDispatch("manager_event", "82485128", r3, r4, r11);
}

namespace {

void TraceUiMethod(std::string_view address, PPCRegister& r3, PPCRegister& r4) {
  if (!UiTraceEnabled()) {
    return;
  }
  const uint32_t vtable = PinyonShiftGuestRangeReadable(r3.u32, 4u)
                              ? LoadGuestU32(r3.u32)
                              : 0u;
  pinyon_shift::diagnostics::RecordEvent(
      "ui.method.enter",
      {{"address", address},
       {"object", Hex32(r3.u32)},
       {"argument", Hex32(r4.u32)},
       {"vtable", Hex32(vtable)}});
  const auto read_field = [&](uint32_t offset) {
    return PinyonShiftGuestRangeReadable(r3.u32 + offset, 4u)
               ? Hex32(LoadGuestU32(r3.u32 + offset))
               : std::string("00000000");
  };
  const auto read_nested = [&](uint32_t field_offset, uint32_t nested_offset) {
    if (!PinyonShiftGuestRangeReadable(r3.u32 + field_offset, 4u)) {
      return std::string("00000000");
    }
    const uint32_t pointer = LoadGuestU32(r3.u32 + field_offset);
    return PinyonShiftGuestRangeReadable(pointer + nested_offset, 4u)
               ? Hex32(LoadGuestU32(pointer + nested_offset))
               : std::string("00000000");
  };
  pinyon_shift::diagnostics::RecordEvent(
      "ui.method.object_fields",
      {{"address", address},
       {"object", Hex32(r3.u32)},
       {"field_12", read_field(12u)},
       {"field_16", read_field(16u)},
       {"field_48", read_field(48u)},
       {"field_52", read_field(52u)},
       {"field_56", read_field(56u)},
       {"field_60", read_field(60u)},
       {"field_88", read_field(88u)},
       {"field_100", read_field(100u)},
       {"field_120", read_field(120u)},
       {"field_124", read_field(124u)},
       {"field_60_word0", read_nested(60u, 0u)},
       {"field_60_word4", read_nested(60u, 4u)},
       {"field_88_word0", read_nested(88u, 0u)}});
  if (!PinyonShiftGuestRangeReadable(r4.u32, 4u)) {
    return;
  }
  for (uint32_t offset = 0; offset < 64u; offset += 4u) {
    const uint32_t value = LoadGuestU32(r4.u32 + offset);
    if (value < 0x82000000u || value >= 0x83000000u) {
      continue;
    }
    const std::string text = PinyonShiftReadGuestAscii(value, 64u);
    if (!text.empty()) {
      pinyon_shift::diagnostics::RecordEvent(
          "ui.method.argument_string",
          {{"address", address},
           {"offset", Hex32(offset)},
           {"value", text}});
    }
  }
}

}  // namespace

void PinyonShiftTraceUiRegistryMethod(PPCRegister& r3, PPCRegister& r4) {
  TraceUiMethod("826413C8", r3, r4);
  if (!UiTraceEnabled() || !PinyonShiftGuestRangeReadable(r4.u32, 2820u)) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "ui.registry.attached",
      {{"address", "826413C8"},
       {"owner", Hex32(r3.u32)},
       {"registry", Hex32(r4.u32)}});
  std::array<std::string, 192> seen{};
  size_t seen_count = 0;
  for (uint32_t offset = 0;
       offset + 4u <= 2820u && seen_count < seen.size(); offset += 4u) {
    const uint32_t pointer = LoadGuestU32(r4.u32 + offset);
    if (pointer < 0x82000000u || pointer >= 0x83000000u) {
      continue;
    }
    const std::string name = PinyonShiftReadGuestAscii(pointer, 64u);
    if (name.empty() ||
        std::find(seen.begin(), seen.begin() + seen_count, name) !=
            seen.begin() + seen_count) {
      continue;
    }
    seen[seen_count++] = name;
    pinyon_shift::diagnostics::RecordEvent(
        "ui.registry.attached_name",
        {{"address", "826413C8"},
         {"registry", Hex32(r4.u32)},
         {"offset", Hex32(offset)},
         {"value", Hex32(pointer)},
         {"name", name}});
  }
}

void PinyonShiftTraceUiResourceMethod(PPCRegister& r3, PPCRegister& r4) {
  TraceUiMethod("82E5E0D0", r3, r4);
}

void PinyonShiftTraceUiSceneMethod(PPCRegister& r3, PPCRegister& r4) {
  TraceUiMethod("82E729F8", r3, r4);
}

namespace {

void TraceUiComponentMethod(std::string_view address, PPCRegister& r3,
                            PPCRegister& r4, PPCRegister* value = nullptr) {
  if (!UiTraceEnabled() ||
      g_ui_component_trace_count.fetch_add(1, std::memory_order_relaxed) >=
          512u) {
    return;
  }
  if (value != nullptr) {
    pinyon_shift::diagnostics::RecordEvent(
        "ui.component.method",
        {{"address", address},
         {"object", Hex32(r3.u32)},
         {"slot", Hex32(r4.u32 + 29u)},
         {"argument", Hex32(r4.u32)},
         {"value", Hex32(value->u32)}});
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "ui.component.method",
      {{"address", address},
       {"object", Hex32(r3.u32)},
       {"slot", Hex32(r4.u32 + 29u)},
       {"argument", Hex32(r4.u32)}});
}

}  // namespace

void PinyonShiftTraceUiComponentGet(PPCRegister& r3, PPCRegister& r4) {
  TraceUiComponentMethod("82E5E550", r3, r4);
}

void PinyonShiftTraceUiComponentStore(PPCRegister& r3, PPCRegister& r4,
                                       PPCRegister& r5) {
  TraceUiComponentMethod("82E5E568", r3, r4, &r5);
}

void PinyonShiftTraceUiComponentClear(PPCRegister& r3, PPCRegister& r4) {
  TraceUiComponentMethod("82E5E580", r3, r4);
}

namespace {

void TraceUiListMethod(std::string_view address, PPCRegister& r3,
                       PPCRegister& r4, PPCRegister& r5) {
  if (!UiTraceEnabled() ||
      g_ui_list_trace_count.fetch_add(1, std::memory_order_relaxed) >=
          1024u) {
    return;
  }
  const auto read_field = [&](uint32_t offset) {
    return PinyonShiftGuestRangeReadable(r3.u32 + offset, 4u)
               ? Hex32(LoadGuestU32(r3.u32 + offset))
               : std::string("00000000");
  };
  const auto read_value_field = [&](uint32_t offset) {
    return PinyonShiftGuestRangeReadable(r5.u32 + offset, 4u)
               ? Hex32(LoadGuestU32(r5.u32 + offset))
               : std::string("00000000");
  };
  const auto read_nested_vtable = [&](uint32_t offset) {
    if (!PinyonShiftGuestRangeReadable(r5.u32 + offset, 4u)) {
      return std::string("00000000");
    }
    const uint32_t pointer = LoadGuestU32(r5.u32 + offset);
    return PinyonShiftGuestRangeReadable(pointer, 4u)
               ? Hex32(LoadGuestU32(pointer))
               : std::string("00000000");
  };
  pinyon_shift::diagnostics::RecordEvent(
      "ui.list.method",
      {{"address", address},
       {"object", Hex32(r3.u32)},
       {"argument", Hex32(r4.u32)},
       {"value", Hex32(r5.u32)},
       {"vtable", read_field(0u)},
       {"field_8", read_field(8u)},
       {"field_12", read_field(12u)},
       {"field_32", read_field(32u)},
       {"field_36", read_field(36u)},
       {"field_116", read_field(116u)},
       {"field_120", read_field(120u)},
       {"field_312", read_field(312u)},
       {"value_vtable", read_value_field(0u)},
       {"value_field_4", read_value_field(4u)},
       {"value_field_8", read_value_field(8u)},
       {"value_field_12", read_value_field(12u)},
       {"value_field_364", read_value_field(364u)},
       {"value_field_468", read_value_field(468u)},
       {"value_field_472", read_value_field(472u)},
       {"value_field_476", read_value_field(476u)},
       {"value_field_508", read_value_field(508u)},
       {"value_field_364_vtable", read_nested_vtable(364u)},
       {"value_field_468_vtable", read_nested_vtable(468u)},
       {"value_field_472_vtable", read_nested_vtable(472u)},
       {"value_field_476_vtable", read_nested_vtable(476u)}});

  const uint32_t value_vtable =
      PinyonShiftGuestRangeReadable(r5.u32, 4u) ? LoadGuestU32(r5.u32) : 0u;
  if (value_vtable != 0x8205109Cu && value_vtable != 0x82059E8Cu) {
    return;
  }
  if (g_ui_pause_menu_field_trace_count.fetch_add(
          1, std::memory_order_relaxed) >= 128u) {
    return;
  }
  constexpr std::array<uint32_t, 6> kMenuVtables = {
      0x82063974u, 0x82063A0Cu, 0x8206D3B8u,
      0x8203363Cu, 0x82026B38u, 0x82063CA4u};
  for (uint32_t offset = 4u; offset <= 768u; offset += 4u) {
    if (!PinyonShiftGuestRangeReadable(r5.u32 + offset, 4u)) {
      break;
    }
    const uint32_t pointer = LoadGuestU32(r5.u32 + offset);
    if (!PinyonShiftGuestRangeReadable(pointer, 4u)) {
      continue;
    }
    const uint32_t nested_vtable = LoadGuestU32(pointer);
    if (std::find(kMenuVtables.begin(), kMenuVtables.end(), nested_vtable) ==
        kMenuVtables.end()) {
      continue;
    }
    pinyon_shift::diagnostics::RecordEvent(
        "ui.pause_menu.field",
        {{"owner", Hex32(r5.u32)},
         {"owner_vtable", Hex32(value_vtable)},
         {"offset", Hex32(offset)},
         {"pointer", Hex32(pointer)},
         {"vtable", Hex32(nested_vtable)}});
  }

  const uint32_t list_vtable =
      PinyonShiftGuestRangeReadable(r3.u32, 4u) ? LoadGuestU32(r3.u32) : 0u;
  if (list_vtable != 0x8206D3B8u ||
      g_ui_menu_field_trace_count.fetch_add(1, std::memory_order_relaxed) >=
          128u) {
    return;
  }
  constexpr std::array<uint32_t, 6> kUiVtables = {
      0x82063974u, 0x82063A0Cu, 0x8206D3B8u,
      0x8203363Cu, 0x82026B38u, 0x82063CA4u};
  for (uint32_t offset = 4u; offset <= 512u; offset += 4u) {
    if (!PinyonShiftGuestRangeReadable(r3.u32 + offset, 4u)) {
      break;
    }
    const uint32_t pointer = LoadGuestU32(r3.u32 + offset);
    if (!PinyonShiftGuestRangeReadable(pointer, 4u)) {
      continue;
    }
    const uint32_t nested_vtable = LoadGuestU32(pointer);
    if (std::find(kUiVtables.begin(), kUiVtables.end(), nested_vtable) ==
        kUiVtables.end()) {
      continue;
    }
    pinyon_shift::diagnostics::RecordEvent(
        "ui.menu.field",
        {{"owner", Hex32(r3.u32)},
         {"offset", Hex32(offset)},
         {"pointer", Hex32(pointer)},
         {"vtable", Hex32(nested_vtable)}});
  }
}

}  // namespace

void PinyonShiftTraceUiListMethod(PPCRegister& r3, PPCRegister& r4,
                                  PPCRegister& r5) {
  TraceUiListMethod("82E7CD78", r3, r4, r5);
}

void PinyonShiftTraceUiListMethod2(PPCRegister& r3, PPCRegister& r4,
                                   PPCRegister& r5) {
  TraceUiListMethod("82E77260", r3, r4, r5);
}

void PinyonShiftTraceUiTextValue(PPCRegister& r3, PPCRegister& r4,
                                 PPCRegister& r5) {
  if (!UiTraceEnabled() || !PinyonShiftGuestRangeReadable(r3.u32, 12u)) {
    return;
  }
  if (LoadGuestU32(r3.u32) != 0x82026B38u) {
    return;
  }
  // The receiver may be any of the three verified CUI4TextElement subobjects
  // of an observed pause button; earlier probes only matched +252.
  constexpr std::array<uint32_t, 3> kElementOffsets = {164u, 252u, 264u};
  const uint32_t button_count = std::min<uint32_t>(
      g_ui_experiment_buttons_count.load(std::memory_order_relaxed),
      kUiExperimentTextTargets);
  for (uint32_t index = 0; index < button_count; ++index) {
    const uint32_t button = g_ui_experiment_buttons[index];
    if (button == 0u) {
      continue;
    }
    for (const uint32_t offset : kElementOffsets) {
      if (button + offset != r3.u32) {
        continue;
      }
      if (g_ui_text_value_trace_count.fetch_add(1, std::memory_order_relaxed) >=
          256u) {
        return;
      }
      pinyon_shift::diagnostics::RecordEvent(
          "ui.pause_button.text_set",
          {{"button", Hex32(button)},
           {"element_offset", std::to_string(offset)},
           {"argument_4", Hex32(r4.u32)},
           {"argument_5", Hex32(r5.u32)},
           {"argument_4_ascii", PinyonShiftReadGuestAscii(r4.u32, 32u)},
           {"argument_5_ascii", PinyonShiftReadGuestAscii(r5.u32, 32u)},
           {"field_4", Hex32(LoadGuestU32(r3.u32 + 4u))},
           {"field_8", Hex32(LoadGuestU32(r3.u32 + 8u))}});
      return;
    }
  }
  // Record any other text-element receiver so a miss stays distinguishable
  // from "the helper was never called on this route".
  if (g_ui_text_value_trace_count.fetch_add(1, std::memory_order_relaxed) >=
      256u) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "ui.text.value",
      {{"object", Hex32(r3.u32)},
       {"argument_4", Hex32(r4.u32)},
       {"argument_5", Hex32(r5.u32)},
       {"argument_4_ascii", PinyonShiftReadGuestAscii(r4.u32, 32u)},
       {"argument_5_ascii", PinyonShiftReadGuestAscii(r5.u32, 32u)},
       {"field_4", Hex32(LoadGuestU32(r3.u32 + 4u))},
       {"field_8", Hex32(LoadGuestU32(r3.u32 + 8u))}});
}

void PinyonShiftTraceUiPauseButtonTextGet(PPCRegister& r3,
                                           PPCRegister& r4) {
  if (!UiTraceEnabled() ||
      !PinyonShiftGuestRangeReadable(r3.u32, 116u) ||
      LoadGuestU32(r3.u32) != 0x8203363Cu ||
      g_ui_pause_button_text_get_trace_count.fetch_add(
          1, std::memory_order_relaxed) >= 256u) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "ui.pause_button.text_get",
      {{"button", Hex32(r3.u32)},
       {"argument_4", Hex32(r4.u32)},
       {"field_84", Hex32(LoadGuestU32(r3.u32 + 84u))},
       {"field_88", Hex32(LoadGuestU32(r3.u32 + 88u))},
       {"field_92", Hex32(LoadGuestU32(r3.u32 + 92u))},
       {"field_96", Hex32(LoadGuestU32(r3.u32 + 96u))},
       {"text_vtable", PinyonShiftGuestRangeReadable(r3.u32 + 252u, 4u)
                           ? Hex32(LoadGuestU32(r3.u32 + 252u))
                           : std::string("00000000")}});
}

void TraceUiMenuDispatch(std::string_view address, PPCRegister& r3,
                         PPCRegister& r4, PPCRegister& r5) {
  if (!UiTraceEnabled() ||
      g_ui_menu_dispatch_trace_count.fetch_add(1, std::memory_order_relaxed) >=
          512u) {
    return;
  }
  const auto read = [](uint32_t address) {
    return PinyonShiftGuestRangeReadable(address, 4u)
               ? Hex32(LoadGuestU32(address))
               : std::string("00000000");
  };
  const uint32_t child = PinyonShiftGuestRangeReadable(r3.u32 + 312u, 4u)
                             ? LoadGuestU32(r3.u32 + 312u)
                             : 0u;
  const uint32_t child_subobject = child + 8u;
  const uint32_t child_sub_vtable = PinyonShiftGuestRangeReadable(
                                       child_subobject, 4u)
                                       ? LoadGuestU32(child_subobject)
                                       : 0u;
  pinyon_shift::diagnostics::RecordEvent(
      "ui.menu.dispatch",
      {{"address", address},
       {"object", Hex32(r3.u32)},
       {"argument", Hex32(r4.u32)},
       {"value", Hex32(r5.u32)},
       {"vtable", read(r3.u32)},
       {"child_312", Hex32(child)},
       {"child_vtable", read(child)},
       {"child_subobject", Hex32(child_subobject)},
       {"child_sub_vtable", Hex32(child_sub_vtable)},
       {"child_slot_0", read(child_sub_vtable)},
       {"child_slot_1", read(child_sub_vtable + 4u)},
       {"value_vtable", read(r5.u32)}});
}

void PinyonShiftTraceUiMenuDispatch(PPCRegister& r3, PPCRegister& r4,
                                    PPCRegister& r5) {
  TraceUiMenuDispatch("82806DD0", r3, r4, r5);
}

void PinyonShiftTraceUiMenuDispatch2(PPCRegister& r3, PPCRegister& r4,
                                     PPCRegister& r5) {
  TraceUiMenuDispatch("82806E50", r3, r4, r5);
}

void PinyonShiftTraceUiListConstructed(PPCRegister& r3, PPCRegister& r4,
                                       PPCRegister& r31) {
  if (!UiTraceEnabled()) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "ui.list.constructed",
      {{"address", "828116C8"},
       {"object", Hex32(r3.u32)},
       {"owner", Hex32(r4.u32)},
       {"saved_object", Hex32(r31.u32)},
       {"vtable", PinyonShiftGuestRangeReadable(r31.u32, 4u)
                       ? Hex32(LoadGuestU32(r31.u32))
                       : std::string("00000000")},
      });
}

// Records the contract argument and caller of the PAUSE_MENU_BUTTON factory.
// The return address names the code that resolves the authored contract table,
// which is the seam a bounded insertion probe has to work through.
void PinyonShiftTraceUiButtonFactory(PPCRegister& r3, PPCRegister& r4,
                                     uint64_t& lr) {
  if (!UiTraceEnabled()) {
    return;
  }
  const auto read_field = [&](uint32_t offset) {
    return PinyonShiftGuestRangeReadable(r3.u32 + offset, 4u)
               ? Hex32(LoadGuestU32(r3.u32 + offset))
               : std::string("00000000");
  };
  pinyon_shift::diagnostics::RecordEvent(
      "ui.button.factory",
      {{"address", "82651438"},
       {"argument", Hex32(r3.u32)},
       {"argument_vtable", read_field(0u)},
       {"argument_field_4", read_field(4u)},
       {"argument_field_8", read_field(8u)},
       {"argument_field_12", read_field(12u)},
       {"argument_ascii", PinyonShiftReadGuestAscii(r3.u32, 32u)},
       {"second_argument", Hex32(r4.u32)},
       {"return_address", Hex32(static_cast<uint32_t>(lr))}});
}

void PinyonShiftTraceUiPauseButtonConstructed(PPCRegister& r3,
                                               PPCRegister& r31) {
  const UiExperimentMode experiment = UiExperimentModeValue();
  if (!UiTraceEnabled() && experiment == UiExperimentMode::kNone) {
    return;
  }
  const uint32_t button = r31.u32;
  const uint32_t slot =
      g_ui_pause_button_count.fetch_add(1, std::memory_order_relaxed);
  if (slot < g_ui_pause_buttons.size()) {
    g_ui_pause_buttons[slot] = button;
  }
  if (experiment == UiExperimentMode::kHideFirst && slot == 0u) {
    ++g_ui_experiment_generation;
    if (g_ui_experiment_api
            .SceneReady("pause_menu", g_ui_experiment_generation,
                        &g_ui_experiment_scene) == pinyon_shift::ui::Status::kOk &&
        g_ui_experiment_api.SetVisible(g_ui_experiment_scene,
                                       "pause.menu.first", false) ==
            pinyon_shift::ui::Status::kOk) {
      g_ui_experiment_button = button;
    }
  }
  if (experiment == UiExperimentMode::kTextProbe) {
    if (slot == 0u) {
      ++g_ui_experiment_generation;
      g_ui_experiment_buttons_count.store(0u, std::memory_order_relaxed);
      if (g_ui_experiment_api.SceneReady("pause_menu",
                                         g_ui_experiment_generation,
                                         &g_ui_experiment_scene) ==
          pinyon_shift::ui::Status::kOk) {
        // The probe is read-only; the requested label exercises the host queue
        // so the request path stays covered while the write target is open.
        g_ui_experiment_buttons_queued.store(
            g_ui_experiment_api.SetText(
                g_ui_experiment_scene, "pause.menu.label",
                std::string(kUiExperimentRequestedLabel)) ==
                pinyon_shift::ui::Status::kOk,
            std::memory_order_relaxed);
      }
    }
    const uint32_t index =
        g_ui_experiment_buttons_count.fetch_add(1, std::memory_order_relaxed);
    if (index < kUiExperimentTextTargets &&
        PinyonShiftGuestRangeReadable(button + 164u, 112u)) {
      g_ui_experiment_buttons[index] = button;
    }
  }
  if (!UiTraceEnabled()) {
    return;
  }
  if (g_ui_pause_button_trace_count.fetch_add(1, std::memory_order_relaxed) >=
      128u) {
    return;
  }
  const uint32_t text = button + 252u;
  if (!PinyonShiftGuestRangeReadable(text, 4u)) {
    return;
  }
  const auto read_field = [&](uint32_t offset) {
    return PinyonShiftGuestRangeReadable(text + offset, 4u)
               ? Hex32(LoadGuestU32(text + offset))
               : std::string("00000000");
  };
  const auto read_inline_text = [&]() {
    std::string value;
    value.reserve(16u);
    for (uint32_t offset = 84u; offset < 100u; ++offset) {
      if (!PinyonShiftGuestRangeReadable(text + offset, 1u)) {
        break;
      }
      const uint8_t byte = LoadGuestU8(text + offset);
      if (byte == 0u) {
        break;
      }
      if (byte < 0x20u || byte > 0x7Eu) {
        return std::string();
      }
      value.push_back(static_cast<char>(byte));
    }
    return value;
  };
  pinyon_shift::diagnostics::RecordEvent(
      "ui.pause_button.constructed",
      {{"address", "8264FC08"},
       {"button", Hex32(button)},
       {"text", Hex32(text)},
       {"text_vtable", read_field(0u)},
       {"button_field_84", PinyonShiftGuestRangeReadable(button + 84u, 4u)
                                 ? Hex32(LoadGuestU32(button + 84u))
                                 : std::string("00000000")},
       {"label_resource_vtable",
        PinyonShiftGuestRangeReadable(button + 84u, 4u) &&
                PinyonShiftGuestRangeReadable(LoadGuestU32(button + 84u), 4u)
            ? Hex32(LoadGuestU32(LoadGuestU32(button + 84u)))
            : std::string("00000000")},
       {"button_field_108", PinyonShiftGuestRangeReadable(button + 108u, 4u)
                                  ? Hex32(LoadGuestU32(button + 108u))
                                  : std::string("00000000")},
       {"button_field_112", PinyonShiftGuestRangeReadable(button + 112u, 4u)
                                  ? Hex32(LoadGuestU32(button + 112u))
                                  : std::string("00000000")},
       {"button_field_160", PinyonShiftGuestRangeReadable(button + 160u, 1u)
                                  ? Hex32(LoadGuestU8(button + 160u))
                                  : std::string("00")},
       {"button_field_235", PinyonShiftGuestRangeReadable(button + 235u, 1u)
                                  ? Hex32(LoadGuestU8(button + 235u))
                                  : std::string("00")},
       {"text_field_4", read_field(4u)},
       {"text_field_8", read_field(8u)},
       {"text_field_32", read_field(32u)},
       {"text_field_84", read_field(84u)},
       {"text_field_88", read_field(88u)},
       {"text_field_92", read_field(92u)},
       {"text_field_96", read_field(96u)},
       {"text_inline", read_inline_text()}});
}

// Samples the two embedded 12-byte CUI4TextElement objects of every observed
// pause button. The element layout is verified statically as
// {vptr = 0x82026B38, +4, +8}, so a label lives in that pair or in the object
// it points to. Sampling repeats at a bounded cadence so one run shows both the
// pre-binding and the post-binding state of the same element. This is
// read-only: the earlier probe wrote at button + 336, which is outside the
// 280-byte CPauseMenuButton allocation.
void SampleUiTextPairs() {
  static uint32_t frame_tick = 0;
  static uint32_t samples = 0;
  static uint32_t recorded = 0;
  constexpr uint32_t kSampleIntervalFrames = 30u;
  constexpr uint32_t kMaximumSamples = 60u;
  constexpr uint32_t kMaximumRecordedPairs = 480u;
  // CPauseMenuButton embeds three verified 12-byte CUI4TextElement objects:
  // the grandparent constructor creates +164, the button constructor creates
  // +252 and +264 (sub_827E5150 / sub_8264FBA0).
  constexpr std::array<uint32_t, 3> kTextElementOffsets = {164u, 252u, 264u};
  ++frame_tick;
  if (samples >= kMaximumSamples || frame_tick % kSampleIntervalFrames != 0u) {
    return;
  }
  ++samples;
  const uint32_t count = std::min<uint32_t>(
      g_ui_experiment_buttons_count.load(std::memory_order_relaxed),
      kUiExperimentTextTargets);
  for (uint32_t index = 0; index < count; ++index) {
    const uint32_t button = g_ui_experiment_buttons[index];
    if (button == 0u) {
      continue;
    }
    for (const uint32_t offset : kTextElementOffsets) {
      if (recorded >= kMaximumRecordedPairs) {
        return;
      }
      const uint32_t element = button + offset;
      if (!PinyonShiftGuestRangeReadable(element, 12u) ||
          LoadGuestU32(element) != 0x82026B38u) {
        continue;
      }
      const uint32_t value = LoadGuestU32(element + 4u);
      const uint32_t resource = LoadGuestU32(element + 8u);
      const auto describe = [](uint32_t pointer) {
        if (pointer < 0x10000u ||
            !PinyonShiftGuestRangeReadable(pointer, 4u)) {
          return std::string("-");
        }
        const std::string text = PinyonShiftReadGuestAscii(pointer, 32u);
        return text.empty() ? std::string("-") : text;
      };
      if (offset == kTextElementOffsets[0]) {
        // One bounded dump of the button and its label resource per sample, so
        // a run shows where the visible item text is bound.
        std::string button_words;
        for (uint32_t word = 0u; word <= 32u; word += 4u) {
          button_words += Hex32(LoadGuestU32(button + word));
          button_words.push_back(' ');
        }
        const uint32_t label = PinyonShiftGuestRangeReadable(button + 84u, 4u)
                                   ? LoadGuestU32(button + 84u)
                                   : 0u;
        std::string label_words;
        if (label >= 0x10000u && PinyonShiftGuestRangeReadable(label, 32u)) {
          for (uint32_t word = 0u; word < 32u; word += 4u) {
            label_words += Hex32(LoadGuestU32(label + word));
            label_words.push_back(' ');
          }
        }
        pinyon_shift::diagnostics::RecordEvent(
            "ui.experiment.button_state",
            {{"sample", std::to_string(samples)},
             {"slot", std::to_string(index)},
             {"button", Hex32(button)},
             {"button_words_0_32", button_words},
             {"label_resource", Hex32(label)},
             {"label_words_0_32", label_words},
             {"label_ascii", describe(label)},
             {"label_nested_ascii",
              describe(label >= 0x10000u &&
                               PinyonShiftGuestRangeReadable(label, 4u)
                           ? LoadGuestU32(label)
                           : 0u)}});
      }
      ++recorded;
      pinyon_shift::diagnostics::RecordEvent(
          "ui.experiment.text_pair",
          {{"scene", "pause_menu"},
           {"sample", std::to_string(samples)},
           {"slot", std::to_string(index)},
           {"element_offset", std::to_string(offset)},
           {"element", Hex32(element)},
           {"value", Hex32(value)},
           {"resource", Hex32(resource)},
           {"value_ascii", describe(value)},
           {"resource_ascii", describe(resource)}});
    }
  }
}

// Applies the queued SetText operation by sampling the verified label pair of
// each observed pause button at the title update boundary. The operation is
// drained through the host API so the queue-to-guest plumbing stays exercised
// while the write target is still being established.
void ApplyUiTextProbe() {
  static bool saw_operation = false;
  if (!saw_operation) {
    for (const auto& operation : g_ui_experiment_api.Drain()) {
      if (operation.kind == pinyon_shift::ui::Operation::Kind::kSetText &&
          operation.component_id == "pause.menu.label") {
        saw_operation = true;
      }
    }
    if (!saw_operation) {
      return;
    }
  }
  SampleUiTextPairs();
}

// One bounded search over the readable parts of the UI heap region for a
// literal the running screen displays, plus the objects that point at it. Each
// 4 MiB chunk is validated once with QueryRangeAccess and then read directly,
// so the whole 128 MiB window costs a few tens of milliseconds and runs only
// once per process. `write_literal` is empty for the read-only scan mode.
void ScanAndWriteUiLabel(std::string_view write_literal) {
  static uint32_t cursor = kUiLabelScanBegin;
  static uint32_t rescan_wait = 0;
  static uint32_t total_written = 0;
  const std::string_view literal = UiLabelScanLiteral();
  const uint32_t literal_length = static_cast<uint32_t>(literal.size());
  if (literal_length < 4u || literal_length > 31u) {
    return;
  }
  auto read_byte = [](uint32_t address) { return LoadGuestU8(address); };
  if (cursor >= kUiLabelScanEnd) {
    // Restart the sweep so a string copied later (for example when the pause
    // overlay is built) is still found while the screen is up.
    if (rescan_wait++ < kUiLabelRescanIntervalFrames) {
      return;
    }
    rescan_wait = 0;
    cursor = kUiLabelScanBegin;
  }
  const uint32_t stop =
      std::min(kUiLabelScanEnd, cursor + kUiLabelScanBytesPerFrame);
  for (uint32_t block = cursor; block < stop; block += kUiLabelScanBlockSize) {
    const uint32_t block_end = std::min(stop, block + kUiLabelScanBlockSize);
    if (!PinyonShiftGuestRangeReadable(block, block_end - block)) {
      continue;
    }
    for (uint32_t base = block; base + 8u < block_end; base += 4u) {
      const uint32_t word0 = LoadGuestU32(base);
      const uint32_t word1 = LoadGuestU32(base + 4u);
      const std::array<uint8_t, 8> window = {
          static_cast<uint8_t>(word0 >> 24), static_cast<uint8_t>(word0 >> 16),
          static_cast<uint8_t>(word0 >> 8),  static_cast<uint8_t>(word0),
          static_cast<uint8_t>(word1 >> 24), static_cast<uint8_t>(word1 >> 16),
          static_cast<uint8_t>(word1 >> 8),  static_cast<uint8_t>(word1)};
      for (uint32_t offset = 0; offset < 4u; ++offset) {
        if (window[offset] != static_cast<uint8_t>(literal[0])) {
          continue;
        }
        bool match = true;
        for (uint32_t index = 1; index < literal_length; ++index) {
          const uint32_t position = offset + index;
          const uint8_t byte = position < window.size()
                                   ? window[position]
                                   : read_byte(base + position);
          if (byte != static_cast<uint8_t>(literal[index])) {
            match = false;
            break;
          }
        }
        if (!match) {
          continue;
        }
        const uint32_t address = base + offset;
        // Direct loads only: the address sits inside a block that
        // PinyonShiftGuestRangeReadable already validated, while the strict
        // per-byte helper rejects these pages even though they hold text.
        const auto read_literal = [&](uint32_t at) {
          std::string text;
          text.reserve(literal_length);
          for (uint32_t step = 0; step < literal_length; ++step) {
            const uint8_t byte = LoadGuestU8(at + step);
            if (byte == 0u) {
              break;
            }
            text.push_back(
                static_cast<char>(byte < 0x20u || byte > 0x7Eu ? '.' : byte));
          }
          return text;
        };
        std::string before;
        bool changed = false;
        if (!write_literal.empty() && total_written < kUiLabelMaximumWrites) {
          before = read_literal(address);
          for (uint32_t step = 0; step < literal_length; ++step) {
            const char replacement =
                step < write_literal.size()
                    ? write_literal[step]
                    : write_literal[write_literal.size() - 1u];
            StoreGuestU8(address + step, static_cast<uint8_t>(replacement));
          }
          ++total_written;
          changed = read_literal(address) != before;
        }
        if (total_written <= kUiLabelMaximumWrites) {
          pinyon_shift::diagnostics::RecordEvent(
              "ui.experiment.label_scan",
              {{"literal", std::string(literal)},
               {"address", Hex32(address)},
               {"ascii", read_literal(address)},
               {"replacement", std::string(write_literal)},
               {"before", before},
               {"changed", changed ? "1" : "0"}});
        }
        base += 3u;
        break;
      }
    }
  }
  cursor = stop;
}

void ApplyUiMutationExperiment() {
  const UiExperimentMode mode = UiExperimentModeValue();
  if (mode == UiExperimentMode::kNone) {
    return;
  }
  if (mode == UiExperimentMode::kTextProbe) {
    ApplyUiTextProbe();
    return;
  }
  if (mode == UiExperimentMode::kLabelScan) {
    ScanAndWriteUiLabel(std::string_view{});
    return;
  }
  if (mode == UiExperimentMode::kLabelWrite) {
    ScanAndWriteUiLabel(UiLabelWriteLiteral());
    return;
  }
  if (g_ui_experiment_button == 0u) {
    return;
  }
  if (!g_ui_experiment_applied) {
    for (const auto& operation : g_ui_experiment_api.Drain()) {
      if (operation.kind != pinyon_shift::ui::Operation::Kind::kSetVisible ||
          operation.component_id != "pause.menu.first" || operation.visible) {
        continue;
      }
      const uint32_t button = g_ui_experiment_button;
      const uint8_t before =
          PinyonShiftGuestRangeReadable(button + 160u, 1u)
              ? LoadGuestU8(button + 160u)
              : 0u;
      StoreGuestU8(button + 160u, 0u);
      g_ui_experiment_applied = true;
      pinyon_shift::diagnostics::RecordEvent(
          "ui.experiment.visible_mutation",
          {{"scene", operation.scene.id},
           {"component", operation.component_id},
           {"button", Hex32(button)},
           {"before", Hex32(before)},
           {"after", Hex32(LoadGuestU8(button + 160u))},
           {"api", "SetVisible"},
           {"boundary", "frame"}});
      break;
    }
  }
  if (g_ui_experiment_applied &&
      PinyonShiftGuestRangeReadable(g_ui_experiment_button + 160u, 1u)) {
    StoreGuestU8(g_ui_experiment_button + 160u, 0u);
  }
}

void PinyonShiftTraceFrameTelemetry(PPCRegister& r28, PPCRegister& r31) {
  PROFILE_SIMULATION_TICK();
  ApplyUiMutationExperiment();
  if (r28.u32 == 0) {
    return;
  }

  if (!FrameTelemetryEnabled()) {
    return;
  }

  const uint32_t route_state = LoadGuestU32(r28.u32 + 2404);
  const uint8_t transition_active = LoadGuestU8(r28.u32 + 4168);

  const uint64_t now_ms = static_cast<uint64_t>(
      std::chrono::duration_cast<std::chrono::milliseconds>(
          std::chrono::steady_clock::now().time_since_epoch())
          .count());
  uint64_t previous_ms =
      g_last_frame_telemetry_ms.load(std::memory_order_relaxed);
  if (now_ms - previous_ms < 200 ||
      !g_last_frame_telemetry_ms.compare_exchange_strong(
          previous_ms, now_ms, std::memory_order_relaxed)) {
    return;
  }

  // These fields are read directly by the frame-loop body immediately after
  // this hook. They provide a stable, read-only route-state seed while vehicle
  // object and transform offsets are discovered from differential captures.
  pinyon_shift::diagnostics::RecordEvent(
      "route.telemetry.frame",
      {{"address", "823EDA10"},
       {"frame_root", Hex32(r28.u32)},
       {"route_root", Hex32(r31.u32)},
       {"generation", Hex32(g_title_generation.load(std::memory_order_acquire))},
       {"route_state", Hex32(route_state)},
       {"transition_active", Hex32(transition_active)}});
}

void PinyonShiftObserveSimulationDelta(PPCRegister& f31) {
  const double seconds = f31.f64;
  if (!std::isfinite(seconds) || seconds < 0.0 || seconds > 0.25) {
    PROFILE_SIMULATION_DELTA_INVALID();
    return;
  }
  PROFILE_SIMULATION_TIME_NS(
      static_cast<int64_t>(std::llround(seconds * 1'000'000'000.0)));
}

void PinyonShiftTraceVehiclePose(PPCRegister& r1, PPCRegister& r30,
                                 PPCRegister& r31) {
  if (r31.u32 == 0) {
    return;
  }

  constexpr uint32_t kActiveSlotOffset = 1500;
  constexpr uint32_t kSlotStride = 1056;
  constexpr uint32_t kPositionOffset = 15120;
  constexpr uint32_t kForwardOffset = 15184;
  constexpr float kMaximumPerUpdateDistanceSquared = 100.0f;
  constexpr uint64_t kRebaseSynchronizationMs = 100;
  const uint32_t slot = LoadGuestU32(r31.u32 + kActiveSlotOffset);
  const uint64_t slot_base = static_cast<uint64_t>(r31.u32) +
                             static_cast<uint64_t>(slot) * kSlotStride;
  const uint64_t position_address_64 = slot_base + kPositionOffset;
  const uint64_t forward_address_64 = slot_base + kForwardOffset;
  if (slot > 4095 || forward_address_64 > UINT32_MAX) {
    return;
  }

  const uint32_t position_address = static_cast<uint32_t>(position_address_64);
  const uint32_t forward_address = static_cast<uint32_t>(forward_address_64);
  const uint64_t now_ms = static_cast<uint64_t>(
      std::chrono::duration_cast<std::chrono::milliseconds>(
          std::chrono::steady_clock::now().time_since_epoch())
          .count());
  const uint32_t generation =
      g_title_generation.load(std::memory_order_acquire);
  const VehiclePose observed{
      LoadGuestF32(position_address),
      LoadGuestF32(position_address + 4),
      LoadGuestF32(position_address + 8),
      LoadGuestF32(position_address + 12),
      LoadGuestF32(forward_address),
      LoadGuestF32(forward_address + 4),
      LoadGuestF32(forward_address + 8),
      LoadGuestF32(forward_address + 12),
  };
  VehiclePose effective = observed;
  bool suppressed = false;
  const bool stabilization_enabled =
      REXCVAR_GET(pinyon_shift_stabilize_vehicle_presentation);
  {
    std::lock_guard lock(g_vehicle_hook_sample_mutex);
    auto& state = g_vehicle_presentation_state;
    if (!stabilization_enabled) {
      state = {};
    } else if (!state.valid || state.generation != generation ||
               state.source != r30.u32) {
      if (IsPlausibleVehiclePose(observed)) {
        state = {true, generation, r30.u32, observed};
      }
    } else if (!IsPlausibleVehiclePose(observed)) {
      effective = state.accepted;
      suppressed = true;
      state.pending = false;
    } else if (PositionDistanceSquared(observed, state.accepted) <=
               kMaximumPerUpdateDistanceSquared) {
      state.accepted = observed;
      state.pending = false;
    } else {
      // The title builds this transform in a stack argument block. During a
      // world-cell rebase it exposes the new local pose before the companion
      // camera/world basis is ready. That 31-33-unit mismatch lasts for the
      // two or three frames visible in the supplied recording. Bridge only
      // that synchronization window, then accept a coherent rebased pose;
      // waiting for the local value to return would freeze ordinary driving.
      if (!state.pending ||
          PositionDistanceSquared(observed, state.pending_last) >
              kMaximumPerUpdateDistanceSquared) {
        state.pending = true;
        state.pending_last = observed;
        state.pending_since_ms = now_ms;
      } else {
        state.pending_last = observed;
      }
      if (state.pending &&
          now_ms - state.pending_since_ms >= kRebaseSynchronizationMs) {
        state.accepted = observed;
        state.pending = false;
      } else if (state.pending) {
        effective = state.accepted;
        suppressed = true;
      }
    }
  }

  if (suppressed) {
    StoreVehiclePose(position_address, forward_address, effective);
  }

  pinyon_shift::fh1_render_test::ObserveVehiclePose(effective.x, effective.y,
                                                    effective.z);

  if (suppressed && FrameTelemetryEnabled()) {
    uint64_t previous_discontinuity_ms =
        g_last_vehicle_discontinuity_ms.load(std::memory_order_relaxed);
    if (now_ms - previous_discontinuity_ms >= 100 &&
        g_last_vehicle_discontinuity_ms.compare_exchange_strong(
            previous_discontinuity_ms, now_ms, std::memory_order_relaxed)) {
      pinyon_shift::diagnostics::RecordEvent(
          "vehicle.telemetry.discontinuity",
          {{"address", "82BC5A3C"},
           {"generation", Hex32(generation)},
           {"caller_lr", Hex32(LoadGuestU32(r1.u32 + 392))},
           {"source", Hex32(r30.u32)},
           {"suppressed", "1"},
           {"x", fmt::format("{}", observed.x)},
           {"y", fmt::format("{}", observed.y)},
           {"z", fmt::format("{}", observed.z)},
           {"effective_x", fmt::format("{}", effective.x)},
           {"effective_y", fmt::format("{}", effective.y)},
           {"effective_z", fmt::format("{}", effective.z)}});
    }
  }
  if (!FrameTelemetryEnabled()) {
    return;
  }
  uint64_t previous_ms =
      g_last_vehicle_pose_ms.load(std::memory_order_relaxed);
  if (now_ms - previous_ms < 200 ||
      !g_last_vehicle_pose_ms.compare_exchange_strong(
          previous_ms, now_ms, std::memory_order_relaxed)) {
    return;
  }

  pinyon_shift::diagnostics::RecordEvent(
      "vehicle.telemetry.pose",
      {{"address", "82BC5A3C"},
       {"generation", Hex32(generation)},
       {"caller_lr", Hex32(LoadGuestU32(r1.u32 + 392))},
       {"source", Hex32(r30.u32)},
       {"owner", Hex32(r31.u32)},
       {"slot", fmt::format("{}", slot)},
       {"position_address", Hex32(position_address)},
       {"forward_address", Hex32(forward_address)},
       {"x", fmt::format("{}", effective.x)},
       {"y", fmt::format("{}", effective.y)},
       {"z", fmt::format("{}", effective.z)},
       {"w", fmt::format("{}", effective.w)},
       {"forward_x", fmt::format("{}", effective.forward_x)},
       {"forward_y", fmt::format("{}", effective.forward_y)},
       {"forward_z", fmt::format("{}", effective.forward_z)}});
}

void PinyonShiftTraceBdz82AD8138(PPCRegister& ctr) {
  if (ctr.u32 == 1) {
    pinyon_shift::diagnostics::RecordEvent(
        "bdz.out_of_range", {{"address", "82AD8138"}, {"selector", "6"}});
  }
}

void PinyonShiftTraceSavePayload(PPCRegister& r4, PPCRegister& r5,
                                 PPCRegister& r12) {
  SnapshotSavePayload("encrypted", r4.u32, r5.u32, r12.u32);
}

void PinyonShiftTraceSaveStreamPayload(PPCRegister& r4, PPCRegister& r5,
                                       PPCRegister& r12) {
  SnapshotSavePayload("stream", r4.u32, r5.u32, r12.u32);
}

void PinyonShiftTraceSavePreEncryption(PPCRegister& r4, PPCRegister& r5) {
  SeedCareerCheckpointInSavePayload(r4.u32, r5.u32);
  SnapshotSavePayload("plaintext", r4.u32, r5.u32, 0x82C666D4u);
}

void PinyonShiftRestoreCareerEligibility(PPCRegister& r3, PPCRegister& r4,
                                         PPCRegister& r31) {
  const uint32_t activity = LoadGuestU32(r31.u32 + 196u);
  if (activity == 0u || r3.u32 == 0u) {
    return;
  }

  const uint8_t active = LoadGuestU8(activity + 40u);
  const uint32_t stage = LoadGuestU32(activity + 44u);
  // Stage 1 is the in-progress Viper drive. Its serialized activity and car
  // position do not include the transient route/arrival trigger, so restoring
  // it produces route-less free roam. Only restore boundaries reached after
  // the title completes that drive.
  if (stage != 2u && stage != 7u && stage != 10u) {
    return;
  }

  // sub_8252AA48 reads the per-profile career eligibility byte at
  // r3 + r4 + 80. Merely overriding its return value is enough to reload the
  // saved activity, but leaves later progression gates seeing the byte as
  // false. Repair the actual byte before the title reads it so a restored
  // stage remains eligible to complete normally.
  const uint32_t eligibility_address = r3.u32 + r4.u32 + 80u;
  const uint8_t previous_eligibility = LoadGuestU8(eligibility_address);
  if (previous_eligibility != 0u) {
    return;
  }

  StoreGuestU8(eligibility_address, 1u);
  pinyon_shift::diagnostics::RecordEvent(
      "save.career_checkpoint.eligibility_restore",
      {{"result", "restored"},
       {"owner", Hex32(r31.u32)},
       {"activity", Hex32(activity)},
       {"eligibility_address", Hex32(eligibility_address)},
       {"previous_eligibility", fmt::format("{}", previous_eligibility)},
       {"active", fmt::format("{}", active)},
       {"stage", fmt::format("{}", stage)}});
}

void PinyonShiftRestoreCareerCheckpointGate(PPCRegister& r3,
                                             PPCRegister& r31) {
  const uint32_t activity = LoadGuestU32(r31.u32 + 196u);
  uint8_t active = activity ? LoadGuestU8(activity + 40u) : 0u;
  const uint32_t stage = activity ? LoadGuestU32(activity + 44u) : 0u;
  if (SaveTraceEnabled()) {
    pinyon_shift::diagnostics::RecordEvent(
        "save.career_checkpoint.gate",
        {{"owner", Hex32(r31.u32)},
         {"activity", Hex32(activity)},
         {"gate", fmt::format("{}", r3.u32)},
         {"active", fmt::format("{}", active)},
         {"stage", fmt::format("{}", stage)}});
  }

  // The activity is the durable checkpoint. Preserve the post-read return
  // override for older saves, and emit the established restore marker even
  // when the pre-read eligibility repair made the title's own result true.
  if (active != 1u ||
      (stage != 2u && stage != 7u && stage != 10u)) {
    return;
  }
  const bool gate_forced = r3.u32 == 0u;
  if (gate_forced) {
    r3.u32 = 1u;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "save.career_checkpoint.gate_override",
      {{"result", "restored"},
       {"owner", Hex32(r31.u32)},
       {"activity", Hex32(activity)},
       {"gate_forced", gate_forced ? "1" : "0"},
       {"stage", fmt::format("{}", stage)}});
}

void PinyonShiftPersistPostViperCheckpoint(PPCRegister& r31) {
  const uint32_t activity = LoadGuestU32(r31.u32 + 196u);
  if (activity == 0) {
    return;
  }

  const uint8_t previous_active = LoadGuestU8(activity + 40u);
  const uint32_t previous_stage = LoadGuestU32(activity + 44u);
  if (previous_stage != 1u) {
    return;
  }

  // sub_828D7EB0 has just advanced the live first-time-career controller to
  // stage 2, the Corrado drive to the festival. Mirror that exact boundary to
  // the durable activity before the title's next ordinary profile save.
  StoreGuestU8(activity + 40u, 1u);
  StoreGuestU32(activity + 44u, 2u);
  pinyon_shift::diagnostics::RecordEvent(
      "save.career_checkpoint.advance",
      {{"owner", Hex32(r31.u32)},
       {"activity", Hex32(activity)},
       {"previous_active", fmt::format("{}", previous_active)},
       {"active", "1"},
       {"previous_stage", fmt::format("{}", previous_stage)},
       {"stage", "2"}});
}

void PinyonShiftTracePersistedProfileOwner(PPCRegister& r3, PPCRegister& r26,
                                           PPCRegister& r28, PPCRegister& r30,
                                           PPCRegister& r31) {
  if (!SaveTraceEnabled()) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "save.profile.owner_result",
      {{"address", "825195F4"},
       {"result", Hex32(r3.u32)},
       {"success_flag", Hex32(r26.u32)},
       {"refresh_requested", Hex32(r28.u32)},
       {"content_owner", Hex32(r30.u32)},
       {"profile_owner", Hex32(r31.u32)}});
}

void PinyonShiftTracePersistedProfileResult(PPCRegister& r3,
                                            PPCRegister& r31) {
  if (!SaveTraceEnabled()) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "save.profile.result",
      {{"address", "82568490"},
       {"result", Hex32(r3.u32)},
       {"owner", Hex32(r31.u32)}});
}

void PinyonShiftTraceFrontEndProfileResult(PPCRegister& r3,
                                           PPCRegister& r31) {
  if (!SaveTraceEnabled()) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "save.frontend.profile_result",
      {{"address", "824ED444"},
       {"result", Hex32(r3.u32)},
       {"owner", Hex32(r31.u32)}});
}

void PinyonShiftTraceFrontEndStateResult(PPCRegister& r3, PPCRegister& r29,
                                         PPCRegister& r31) {
  if (!SaveTraceEnabled()) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "save.frontend.state_result",
      {{"address", "827A1DC4"},
       {"result", Hex32(r3.u32)},
       {"payload", Hex32(r29.u32)},
       {"owner", Hex32(r31.u32)}});
}

void PinyonShiftTraceBdz82AD813C(PPCRegister& ctr) {
  if (ctr.u32 == 1) {
    pinyon_shift::diagnostics::RecordEvent(
        "bdz.out_of_range", {{"address", "82AD813C"}, {"selector", "7"}});
  }
}

void PinyonShiftTraceMainLoopExit(PPCRegister& r29, PPCRegister& r30,
                                  PPCRegister& r31) {
  const auto r29_hex = Hex32(r29.u32);
  const auto r30_hex = Hex32(r30.u32);
  const auto r31_hex = Hex32(r31.u32);
  pinyon_shift::diagnostics::RecordEvent(
      "main_loop.exit",
      {{"address", "823EE584"},
       {"r29", r29_hex},
       {"r30", r30_hex},
       {"r31", r31_hex}});
}

void PinyonShiftTraceCleanupPointerCheck(PPCRegister& r31) {
  const uint32_t field = r31.u32 + 684;
  g_cleanup_pointer_field.store(field, std::memory_order_release);
  const uint32_t value = LoadGuestU32(field);
  if (value != 0) {
    g_cleanup_pointer_live.store(true, std::memory_order_release);
  } else if (g_cleanup_pointer_live.exchange(false, std::memory_order_acq_rel)) {
    g_title_generation.fetch_add(1, std::memory_order_acq_rel);
    g_opening_movie_skip_logged.store(false, std::memory_order_release);
  }
  const auto owner_hex = Hex32(r31.u32);
  const auto field_hex = Hex32(field);
  const auto value_hex = Hex32(value);
  pinyon_shift::diagnostics::RecordEvent(
      "cleanup.pointer.check",
      {{"address", "82482264"},
       {"owner", owner_hex},
       {"field", field_hex},
       {"value", value_hex},
       {"generation", Hex32(g_title_generation.load(std::memory_order_acquire))}});
}

void PinyonShiftTraceCleanupPointerWait(PPCRegister& r31) {
  if (r31.u32 !=
      g_cleanup_pointer_field.load(std::memory_order_acquire)) {
    return;
  }
  const auto field_hex = Hex32(r31.u32);
  const auto value_hex = Hex32(LoadGuestU32(r31.u32));
  pinyon_shift::diagnostics::RecordEvent(
      "cleanup.pointer.wait",
      {{"address", "8247D534"},
       {"field", field_hex},
       {"value", value_hex}});
}

static bool PinyonShiftGuestRangeReadable(uint32_t address, uint32_t size) {
  if (size == 0) {
    return true;
  }
  const uint32_t end = address + size - 1u;
  auto* memory = rex::system::kernel_state()->memory();
  auto* heap = end >= address ? memory->LookupHeap(address) : nullptr;
  if (!heap || heap->QueryRangeAccess(address, end) ==
                   rex::memory::PageAccess::kNoAccess) {
    return false;
  }

  // QueryRangeAccess reflects the guest heap's page-table metadata. A stale
  // relocated geometry pointer can still land in a reserved or decommitted
  // host page whose guest metadata looks readable, and the generated load
  // dereferences the host mapping directly. Verify every host page touched by
  // the range as well so the validation hook cannot itself raise a read AV.
  const size_t page_size = rex::memory::page_size();
  uint64_t cursor = address;
  while (cursor <= end) {
    auto* host_address =
        memory->TranslateVirtual(static_cast<uint32_t>(cursor));
    size_t region_length = page_size;
    rex::memory::PageAccess host_access =
        rex::memory::PageAccess::kNoAccess;
    if (!rex::memory::QueryProtect(host_address, region_length, host_access) ||
        host_access == rex::memory::PageAccess::kNoAccess) {
      return false;
    }

    const uintptr_t host_value =
        reinterpret_cast<uintptr_t>(host_address);
    const size_t page_remaining =
        page_size - (host_value % page_size);
    const uint64_t range_remaining =
        static_cast<uint64_t>(end) - cursor + 1u;
    cursor += std::min<uint64_t>(range_remaining, page_remaining);
  }
  return true;
}

static std::string PinyonShiftReadGuestAscii(uint32_t address,
                                             uint32_t maximum_length) {
  if (maximum_length == 0 || !PinyonShiftGuestRangeReadable(address, 1u)) {
    return {};
  }
  std::string value;
  value.reserve(maximum_length);
  for (uint32_t offset = 0; offset < maximum_length; ++offset) {
    if (!PinyonShiftGuestRangeReadable(address + offset, 1u)) {
      return {};
    }
    const uint8_t character = LoadGuestU8(address + offset);
    if (character == 0) {
      return value.size() >= 3 ? value : std::string{};
    }
    if (character < 0x20 || character > 0x7E) {
      return {};
    }
    value.push_back(static_cast<char>(character));
  }
  return {};
}

void PinyonShiftValidateGeometryOutput(PPCRegister& r4, PPCRegister& r5,
                                       PPCRegister& r6) {
  // Every caller-owned result slot is 544 bytes. sub_82D3CD48's variable
  // vector writes fit that slot only while (count + 15) * 16 <= 544, so 19 is
  // the largest representable count. Redirecting an oversized result to a
  // shared discard buffer avoids the immediate write AV but leaves the caller
  // consuming a missing result and permits its outer loop to continue through
  // corrupted entries. Normalize the invalid serialized count instead; the
  // independent lookup hook still repairs an unreadable three-byte pointer.
  constexpr uint32_t kMaximumIndexCount = 19u;
  const uint32_t count = LoadGuestU8(r5.u32 + 4u);
  if (count <= kMaximumIndexCount) {
    return;
  }

  StoreGuestU8(r5.u32 + 4u, 0u);
  pinyon_shift::diagnostics::RecordEvent(
      "geometry.entry.oversized_count_repair",
      {{"address", "82D3CD58"},
       {"consumer", "82D3CD58"},
       {"owner", Hex32(r4.u32)},
       {"entry", Hex32(r5.u32)},
       {"count", Hex32(count)},
       {"maximum", Hex32(kMaximumIndexCount)},
       {"output", Hex32(r6.u32)}});
}

static uint32_t PinyonShiftGeometryZeroIndexBuffer() {
  uint32_t buffer =
      g_geometry_zero_index_buffer.load(std::memory_order_acquire);
  if (buffer != 0) {
    return buffer;
  }

  std::lock_guard lock(g_geometry_zero_index_buffer_mutex);
  buffer = g_geometry_zero_index_buffer.load(std::memory_order_relaxed);
  if (buffer != 0) {
    return buffer;
  }

  constexpr uint32_t kMaximumIndexCount = 256u;
  auto* memory = rex::system::kernel_state()->memory();
  buffer = memory->SystemHeapAlloc(kMaximumIndexCount, 16u);
  for (uint32_t index = 0; index < kMaximumIndexCount; ++index) {
    StoreGuestU8(buffer + index, 0u);
  }
  g_geometry_zero_index_buffer.store(buffer, std::memory_order_release);
  return buffer;
}

void PinyonShiftValidateGeometryLookup(PPCRegister& r4, PPCRegister& r5,
                                       PPCRegister& r6, PPCRegister& r11) {
  // sub_82D3CD48 consumes at least three byte indices from the pointer at
  // entry+0 before consulting the count at entry+4. Existing-save replay has
  // exposed multiple stale relocated pointers here, including the exact-build
  // 0x6CD00200 read AV. Preserve valid triplets. For an unreadable triplet,
  // redirect the entry to a process-lifetime zero-index buffer large enough
  // for the full uint8 count. The function reloads entry+0 in its later
  // variable-length loop, so repairing only r11 is insufficient. Preserve the
  // original count: changing it alters the caller's output sizing decisions.
  constexpr uint32_t kTripletSize = 3u;
  if (PinyonShiftGuestRangeReadable(r11.u32, kTripletSize)) {
    return;
  }

  const uint32_t original_pointer = r11.u32;
  const uint32_t original_count = LoadGuestU8(r5.u32 + 4u);
  const uint32_t fallback = PinyonShiftGeometryZeroIndexBuffer();
  StoreGuestU32(r5.u32, fallback);
  r11.u64 = fallback;

  pinyon_shift::diagnostics::RecordEvent(
      "geometry.lookup.unreadable_triplet_repair",
      {{"address", "82D3CD80"},
       {"consumer", "82D3CD80"},
       {"owner", Hex32(r4.u32)},
       {"entry", Hex32(r5.u32)},
       {"output", Hex32(r6.u32)},
       {"count", Hex32(original_count)},
       {"pointer", Hex32(original_pointer)},
       {"fallback", Hex32(fallback)}});
}

static bool PinyonShiftGeometryIndexListReadable(uint32_t list,
                                                 uint32_t count) {
  return PinyonShiftGuestRangeReadable(list, count);
}

void PinyonShiftValidateGeometryIndexList(PPCRegister& r8, PPCRegister& r29,
                                          PPCRegister& r31) {
  // sub_82D3DA48 relocates the geometry blob's entry pointers in place. Each
  // entry contains a byte count at +9 and the corresponding byte-index list at
  // +4. Continuation captures have observed both a null list and an
  // uncommitted list while the count remained nonzero. Treat only an unreadable
  // complete list as empty, preserving all valid geometry data and recording
  // the repaired serialized-blob invariant.
  const uint32_t count = r8.u32 & 0xFFu;
  if (count == 0) {
    return;
  }

  const uint32_t list = LoadGuestU32(r29.u32 + 4u);
  // sub_82D3DB00 reserves eight 544-byte result slots in its 4,544-byte
  // frame. A larger serialized count walks r6 beyond that array and also
  // indexes unrelated lookup-table entries. Treat the whole invalid list as
  // empty rather than preserving an arbitrary prefix of corrupted geometry.
  constexpr uint32_t kMaximumResultCount = 8u;
  if (count > kMaximumResultCount) {
    // Persist the repair in the transient relocated entry. Register-only
    // suppression leaves the invalid pair live and caused the same entry to be
    // repaired repeatedly during the long-play soak test.
    StoreGuestU8(r29.u32 + 9u, 0u);
    r8.u64 = 0;
    pinyon_shift::diagnostics::RecordEvent(
        "geometry.index.oversized_list_repair",
        {{"address", "82D3DB54"},
         {"consumer", "82D3DB6C"},
         {"owner", Hex32(r31.u32)},
         {"entry", Hex32(r29.u32)},
         {"count_address", Hex32(r29.u32 + 9u)},
         {"count", Hex32(count)},
         {"maximum", Hex32(kMaximumResultCount)},
         {"list", Hex32(list)},
         {"repair", "entry_count_zeroed"}});
    return;
  }

  if (PinyonShiftGeometryIndexListReadable(list, count)) {
    return;
  }

  StoreGuestU8(r29.u32 + 9u, 0u);
  r8.u64 = 0;
  pinyon_shift::diagnostics::RecordEvent(
      "geometry.index.unreadable_list_repair",
      {{"address", "82D3DB54"},
       {"consumer", "82D3DB6C"},
        {"owner", Hex32(r31.u32)},
        {"entry", Hex32(r29.u32)},
        {"count_address", Hex32(r29.u32 + 9u)},
        {"count", Hex32(count)},
        {"list", Hex32(list)},
        {"repair", "entry_count_zeroed"}});
}

void PinyonShiftValidateGeometrySecondaryIndexList(PPCRegister& r6,
                                                   PPCRegister& r29,
                                                   PPCRegister& r31) {
  // The same 12-byte entry contains a second byte-index list at +0 with its
  // count at +8. The first field replay that exercised the primary-list repair
  // immediately reached this sibling loop with the same invalid serialized
  // invariant. Validate it independently so repairing +4/+9 cannot fall
  // through to an equivalent read at 0x82D3DC1C.
  const uint32_t count = r6.u32 & 0xFFu;
  if (count == 0) {
    return;
  }

  const uint32_t list = LoadGuestU32(r29.u32);
  if (PinyonShiftGeometryIndexListReadable(list, count)) {
    return;
  }

  // Make the repaired invariant durable for every consumer of this relocated
  // entry, rather than suppressing only the current loop iteration.
  StoreGuestU8(r29.u32 + 8u, 0u);
  r6.u64 = 0;
  pinyon_shift::diagnostics::RecordEvent(
      "geometry.index.unreadable_secondary_list_repair",
      {{"address", "82D3DBF4"},
       {"consumer", "82D3DC1C"},
        {"owner", Hex32(r31.u32)},
        {"entry", Hex32(r29.u32)},
        {"count_address", Hex32(r29.u32 + 8u)},
        {"count", Hex32(count)},
        {"list", Hex32(list)},
        {"repair", "entry_count_zeroed"}});
}

void PinyonShiftTraceGeometryIndex(PPCRegister& r9, PPCRegister& r11,
                                   PPCRegister& r29, PPCRegister& r30,
                                   PPCRegister& r31) {
  // Runs immediately before the byte read at 0x82D3DB6C. Runs 103 and the
  // generation-contract regression both reached this instruction with an
  // uncommitted 0x25xxxxxx list pointer. Keep the hook observational: the
  // first-chance AV handler remains responsible for preserving the fault.
  if ((r11.u32 & 0xF0000000u) >= 0x40000000u) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "geometry.index.suspicious",
      {{"address", "82D3DB6C"},
       {"owner", Hex32(r31.u32)},
       {"entry", Hex32(r29.u32)},
       {"index", Hex32(r30.u32)},
       {"list", Hex32(r11.u32)},
       {"lookup_table", Hex32(r9.u32)}});
}

void PinyonShiftTraceRetainVtable(PPCRegister& r4, PPCRegister& r11,
                                  PPCRegister& r30, PPCRegister& r31) {
  // sub_826E1B10 is a shared/intrusive pointer assignment helper. At
  // 0x826E1B3C it is about to load the AddRef target from vtable+8. PID 25180
  // reached this instruction with a readable object whose vtable was 0x487C,
  // causing the authoritative read AV at guest 0x4884. Keep this hook
  // observational and narrowly log only pointers outside the title image.
  if (!FrameTelemetryEnabled() ||
      (r11.u32 >= 0x82000000u && r11.u32 < 0x84000000u)) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "object.retain.invalid_vtable",
      {{"address", "826E1B3C"},
       {"destination", Hex32(r30.u32)},
       {"source_slot", Hex32(r4.u32)},
       {"object", Hex32(r31.u32)},
       {"vtable", Hex32(r11.u32)}});
}

void PinyonShiftTraceRetainSourceSlot(PPCRegister& r3, PPCRegister& r4,
                                      PPCRegister& r26, PPCRegister& r27,
                                      PPCRegister& r29, PPCRegister& r31) {
  // PID 31612 reached sub_826E1B10 from this call site with source slot
  // 0x43D29E00. The owner inferred from its destination is normal in clean
  // replays, so retain only this direct source-slot correlation for a future
  // failing run. This executes immediately before the helper call.
  if (!FrameTelemetryEnabled() || r4.u32 != 0x43D29E00u) {
    return;
  }
  pinyon_shift::diagnostics::RecordEvent(
      "object.retain.source_slot",
      {{"address", "82C6DFA8"},
       {"destination", Hex32(r3.u32)},
       {"source_slot", Hex32(r4.u32)},
       {"state", Hex32(r26.u32)},
       {"table_base", Hex32(r27.u32)},
       {"slot_index", Hex32(r29.u32)},
       {"owner", Hex32(r31.u32)}});
}
