#include "native_renderer/graphics_hooks.h"

#include <array>
#include <mutex>
#include <set>

#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/ppc/context.h>

#include <rex/perf/counter.h>
#include <rex/system/interfaces/graphics.h>

#include "native_renderer/fh1_gpu_corpus.h"

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
void PinyonShiftObserveGraphicsFrame() { PROFILE_SOURCE_FRAME(); }

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
