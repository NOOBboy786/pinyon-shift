#include <rex/system/interfaces/graphics.h>

#include "fh1_render_test.h"
#include "native_renderer/guest_output_renderer.h"

namespace {

bool ObserveRenderTestOutput(
    const rex::system::NativeGuestOutputRenderContext& context) {
  return pinyon_shift::fh1_render_test::ObserveOutput(context);
}

}  // namespace

namespace pinyon_shift::native_renderer {

void InstallGuestOutputRenderer(rex::system::IGraphicsSystem* graphics_system) {
  if (graphics_system) {
    graphics_system->SetNativeGuestOutputRenderer(
        fh1_render_test::Enabled() ? &ObserveRenderTestOutput : nullptr);
  }
}

void UninstallGuestOutputRenderer(
    rex::system::IGraphicsSystem* graphics_system) {
  if (graphics_system) {
    graphics_system->SetNativeGuestOutputRenderer(nullptr);
  }
}

}  // namespace pinyon_shift::native_renderer
