#include <cassert>

#include "native_renderer/fh1_pass_tracker.h"

using pinyon_shift::native_renderer::Fh1PassTracker;

namespace {

rex::system::GraphicsFh1ExecutionKey Draw(uint64_t attachment,
                                         uint64_t pipeline) {
  rex::system::GraphicsFh1ExecutionKey key;
  key.shader_state = 1;
  key.pipeline_state = pipeline;
  key.attachment_state = attachment;
  key.operation_state = 2;
  key.identity = key.ComputeIdentity();
  return key;
}

rex::system::GraphicsFh1ExecutionKey Copy(uint64_t attachment,
                                         uint64_t operation) {
  rex::system::GraphicsFh1ExecutionKey key;
  key.kind = rex::system::GraphicsFh1ExecutionKind::kCopyResolve;
  key.attachment_state = attachment;
  key.operation_state = operation;
  key.identity = key.ComputeIdentity();
  return key;
}

}  // namespace

int main() {
  Fh1PassTracker tracker;
  assert(!tracker.ObserveDraw(Draw(10, 20), 1, 100));
  assert(!tracker.ObserveDraw(Draw(10, 21), 1, 200));
  const auto copied = tracker.ObserveCopy(Copy(10, 30), 1);
  assert(copied && copied->draw_count == 2 && copied->first_draw_family &&
         copied->first_draw_identity == Draw(10, 20).identity &&
         copied->terminal_copy_state && copied->prepare_cpu_time_ns == 300);

  Fh1PassTracker repeated;
  repeated.ObserveDraw(Draw(10, 20), 7);
  repeated.ObserveDraw(Draw(10, 21), 7);
  const auto repeated_copy = repeated.ObserveCopy(Copy(10, 30), 7);
  assert(repeated_copy && repeated_copy->signature == copied->signature &&
         repeated_copy->first_draw_family == copied->first_draw_family);

  Fh1PassTracker split;
  split.ObserveDraw(Draw(10, 20), 1);
  const auto attachment_break = split.ObserveDraw(Draw(11, 21), 1);
  assert(attachment_break && attachment_break->draw_count == 1 &&
         !attachment_break->terminal_copy_state);
  const auto frame_break = split.ObserveDraw(Draw(11, 22), 2);
  assert(frame_break && frame_break->draw_count == 1);
  assert(split.Finish());
}
