#pragma once

#include <functional>
#include <memory>

namespace rex {
struct RuntimeConfig;
namespace system {
class IGraphicsSystem;
struct NativeGuestOutputRenderContext;
class XThread;
}  // namespace system
namespace ui {
class Window;
class WindowedAppContext;
}  // namespace ui
}  // namespace rex

namespace pinyon_shift::fh1_render_test {

// Loads the optional FH1-only scripted render test and replaces physical input
// with its deterministic controller stream. Invalid requests fail the process.
void Configure(rex::RuntimeConfig& config);
bool Enabled();

// Called at the final guest-output boundary. Returns false because validation
// observes the real output and never claims or modifies it.
bool ObserveOutput(const rex::system::NativeGuestOutputRenderContext& context);

// Records FH1's active vehicle presentation transform for timing validation.
// This is consumed only by the deterministic render-test capture events.
void ObserveVehiclePose(float x, float y, float z);

void Start(rex::system::IGraphicsSystem* graphics_system,
           rex::ui::WindowedAppContext* app_context, rex::ui::Window* window,
           std::function<void()> before_close = {});
void Stop();

}  // namespace pinyon_shift::fh1_render_test
