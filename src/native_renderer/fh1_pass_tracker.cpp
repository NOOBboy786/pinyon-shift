#include "native_renderer/fh1_pass_tracker.h"

namespace pinyon_shift::native_renderer {
namespace {

constexpr uint64_t kHashSeed = UINT64_C(0xCBF29CE484222325);

void AppendHash(uint64_t& hash, uint64_t value) {
  for (uint32_t byte = 0; byte < 8; ++byte) {
    hash ^= uint8_t(value >> (byte * 8));
    hash *= UINT64_C(0x100000001B3);
  }
}

uint64_t DrawFamily(
    const rex::system::GraphicsFh1ExecutionKey& key) {
  uint64_t family = kHashSeed;
  AppendHash(family, key.shader_state);
  AppendHash(family, key.pipeline_state);
  AppendHash(family, key.operation_state);
  return family;
}

}  // namespace

std::optional<Fh1PassSummary> Fh1PassTracker::ObserveDraw(
    const rex::system::GraphicsFh1ExecutionKey& key, uint64_t frame,
    uint64_t prepare_cpu_time_ns) {
  if (key.kind != rex::system::GraphicsFh1ExecutionKind::kDraw) {
    return std::nullopt;
  }
  std::optional<Fh1PassSummary> finished;
  if (current_.draw_count &&
      (current_.frame != frame ||
       current_.attachment_state != key.attachment_state)) {
    finished = Finish(0);
  }
  if (!current_.draw_count) {
    current_.frame = frame;
    current_.attachment_state = key.attachment_state;
    current_.first_draw_family = DrawFamily(key);
    current_.first_draw_identity = key.identity;
    running_signature_ = kHashSeed;
    AppendHash(running_signature_, current_.attachment_state);
  }
  AppendHash(running_signature_, DrawFamily(key));
  ++current_.draw_count;
  current_.prepare_cpu_time_ns += prepare_cpu_time_ns;
  current_.hazard_flags |= key.hazard_flags;
  return finished;
}

std::optional<Fh1PassSummary> Fh1PassTracker::ObserveCopy(
    const rex::system::GraphicsFh1ExecutionKey& key, uint64_t frame) {
  if (key.kind != rex::system::GraphicsFh1ExecutionKind::kCopyResolve ||
      !current_.draw_count || current_.frame != frame) {
    return std::nullopt;
  }
  uint64_t terminal_copy_state = kHashSeed;
  AppendHash(terminal_copy_state, key.attachment_state);
  AppendHash(terminal_copy_state, key.operation_state);
  return Finish(terminal_copy_state);
}

std::optional<Fh1PassSummary> Fh1PassTracker::Finish() {
  return Finish(0);
}

std::optional<Fh1PassSummary> Fh1PassTracker::Finish(
    uint64_t terminal_copy_state) {
  if (!current_.draw_count) {
    return std::nullopt;
  }
  current_.terminal_copy_state = terminal_copy_state;
  AppendHash(running_signature_, terminal_copy_state);
  current_.signature = running_signature_ ? running_signature_ : 1;
  Fh1PassSummary finished = current_;
  current_ = {};
  running_signature_ = 0;
  return finished;
}

}  // namespace pinyon_shift::native_renderer
