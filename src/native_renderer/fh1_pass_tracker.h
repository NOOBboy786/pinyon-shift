#pragma once

#include <cstdint>
#include <optional>

#include <rex/system/interfaces/graphics.h>

namespace pinyon_shift::native_renderer {

struct Fh1PassSummary {
  uint64_t signature = 0;
  uint64_t frame = 0;
  uint64_t attachment_state = 0;
  uint64_t first_draw_family = 0;
  uint64_t first_draw_identity = 0;
  uint64_t terminal_copy_state = 0;
  uint64_t prepare_cpu_time_ns = 0;
  uint32_t draw_count = 0;
  uint32_t hazard_flags = 0;

  bool operator==(const Fh1PassSummary&) const = default;
};

class Fh1PassTracker {
 public:
  std::optional<Fh1PassSummary> ObserveDraw(
      const rex::system::GraphicsFh1ExecutionKey& key, uint64_t frame,
      uint64_t prepare_cpu_time_ns = 0);
  std::optional<Fh1PassSummary> ObserveCopy(
      const rex::system::GraphicsFh1ExecutionKey& key, uint64_t frame);
  std::optional<Fh1PassSummary> Finish();

 private:
  std::optional<Fh1PassSummary> Finish(uint64_t terminal_copy_state);

  Fh1PassSummary current_{};
  uint64_t running_signature_ = 0;
};

}  // namespace pinyon_shift::native_renderer
