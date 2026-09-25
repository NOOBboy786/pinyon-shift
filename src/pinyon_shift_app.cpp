#include "pinyon_shift_app.h"
#include "pinyon_shift_init.h"

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <Windows.h>
#include <dxgi.h>
#include <tlhelp32.h>

#include <chrono>
#include <cwchar>
#include <filesystem>
#include <fstream>
#include <regex>
#include <sstream>
#include <string>
#include <system_error>
#include <thread>
#include <unordered_set>

#include <fmt/format.h>
#include <rex/cvar.h>
#include <rex/logging.h>
#include <rex/perf/counter.h>
#include <rex/runtime.h>
#include <rex/system/kernel_state.h>
#include <rex/system/xthread.h>
#include <rex/thread.h>

#include "pinyon_shift_diagnostics.h"
#include "pinyon_shift_hitch_logger.h"
#include "pinyon_shift_thread_scheduler.h"

#include <cstdio>

REXCVAR_DEFINE_UINT32(pinyon_shift_config_schema, 4, "Pinyon Shift",
                      "Pinyon Shift host configuration schema version");
REXCVAR_DEFINE_BOOL(pinyon_shift_capture_performance, true, "Pinyon Shift",
                    "Capture lightweight per-frame performance counters to a session CSV");

namespace {

constexpr uint32_t kConfigSchema = 4;

bool EnsureSupportedConfig(const std::filesystem::path& path, bool& created,
                           bool& migrated) {
  created = false;
  migrated = false;
  if (!std::filesystem::exists(path)) {
    std::ofstream output(path, std::ios::binary | std::ios::trunc);
    if (!output) {
      return false;
    }
    output << "# Pinyon Shift host configuration.\n"
              "# Increment this only with an explicit migration.\n"
              "# Controller support with keyboard emulation as a fallback.\n"
              "pinyon_shift_config_schema = "
           << kConfigSchema << "\n"
              "input_backend = \"sdl\"\n"
              "hid_mappings_file = \"gamecontrollerdb.txt\"\n"
              "mnk_mode = true\n"
              "keybind_a = \"LMB,Space\"\n"
              "keybind_start = \"Return\"\n"
              "d3d12_allow_variable_refresh_rate_and_tearing = true\n"
              "pinyon_shift_capture_performance = true\n"
              "pinyon_shift_stabilize_vehicle_presentation = false\n"
              "pinyon_shift_skip_opening_movies = true\n"
              "resolution = \"720p\"\n"
              "video_mode_width = 1280\n"
              "video_mode_height = 720\n"
              "anisotropic_override = 2\n"
              "swap_post_effect = \"none\"\n"
              "draw_resolution_scale_x = 1\n"
              "draw_resolution_scale_y = 1\n"
              "d3d12_submit_on_primary_buffer_end = true\n"
              "clear_memory_page_state = false\n";
    created = true;
    return output.good();
  }

  std::ifstream input(path, std::ios::binary);
  if (!input) {
    return false;
  }
  std::ostringstream contents;
  contents << input.rdbuf();
  input.close();
  const std::string config_text = contents.str();
  const std::regex schema_pattern(
      R"((?:^|\n)\s*pinyon_shift_config_schema\s*=\s*([0-9]+)\s*(?:#.*)?(?:\r?\n|$))");
  std::smatch match;
  if (!std::regex_search(config_text, match, schema_pattern) || match.size() != 2) {
    return false;
  }
  try {
    const uint32_t schema = std::stoul(match[1].str());
    if (schema == kConfigSchema) {
      return true;
    }
    if (schema < 1 || schema > 3) {
      return false;
    }

    std::filesystem::path backup = path;
    backup += L".schema" + std::to_wstring(schema) + L".bak";
    std::error_code backup_error;
    std::filesystem::copy_file(path, backup,
                               std::filesystem::copy_options::skip_existing,
                               backup_error);
    if (backup_error && backup_error != std::errc::file_exists) {
      return false;
    }

    std::string migrated_text = config_text;
    migrated_text.replace(static_cast<size_t>(match.position(1)),
                          static_cast<size_t>(match.length(1)),
                          std::to_string(kConfigSchema));
    if (schema == 1) {
      const std::regex stabilization_pattern(
          R"((?:^|\n)\s*pinyon_shift_stabilize_vehicle_presentation\s*=\s*(true|false)\s*(?:#.*)?(?:\r?\n|$))");
      std::smatch stabilization_match;
      if (std::regex_search(migrated_text, stabilization_match,
                            stabilization_pattern)) {
        migrated_text.replace(
            static_cast<size_t>(stabilization_match.position(1)),
            static_cast<size_t>(stabilization_match.length(1)), "false");
      } else {
        if (!migrated_text.empty() && migrated_text.back() != '\n') {
          migrated_text.push_back('\n');
        }
        migrated_text +=
            "pinyon_shift_stabilize_vehicle_presentation = false\n";
      }
    }

    const std::regex accept_binding_pattern(
        R"((?:^|\n)\s*keybind_a\s*=\s*\"[^\"]*\"\s*(?:#.*)?(?:\r?\n|$))");
    if (!std::regex_search(migrated_text, accept_binding_pattern)) {
      if (!migrated_text.empty() && migrated_text.back() != '\n') {
        migrated_text.push_back('\n');
      }
      migrated_text += "keybind_a = \"LMB,Space\"\n";
    }

    const std::pair<const char*, const char*> graphics_settings[] = {
        {"anisotropic_override", "anisotropic_override = 2\n"},
        {"swap_post_effect", "swap_post_effect = \"none\"\n"},
        {"draw_resolution_scale_x", "draw_resolution_scale_x = 1\n"},
        {"draw_resolution_scale_y", "draw_resolution_scale_y = 1\n"},
        {"resolution", "resolution = \"720p\"\n"},
        {"video_mode_width", "video_mode_width = 1280\n"},
        {"video_mode_height", "video_mode_height = 720\n"},
        {"d3d12_submit_on_primary_buffer_end", "d3d12_submit_on_primary_buffer_end = true\n"},
        {"clear_memory_page_state", "clear_memory_page_state = false\n"},
        {"d3d12_allow_variable_refresh_rate_and_tearing", "d3d12_allow_variable_refresh_rate_and_tearing = true\n"},
    };
    for (const auto& [name, line] : graphics_settings) {
      const std::regex setting_pattern("(?:^|\\n)\\s*" + std::string(name) +
                                       "\\s*=", std::regex::icase);
      if (!std::regex_search(migrated_text, setting_pattern)) {
        if (!migrated_text.empty() && migrated_text.back() != '\n') {
          migrated_text.push_back('\n');
        }
        migrated_text += line;
      }
    }

    std::filesystem::path temporary = path;
    temporary += L".migrating";
    {
      std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
      if (!output) {
        return false;
      }
      output << migrated_text;
      if (!output.good()) {
        return false;
      }
    }
    if (!MoveFileExW(temporary.c_str(), path.c_str(),
                     MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
      std::error_code error;
      std::filesystem::remove(temporary, error);
      return false;
    }
    migrated = true;
    return true;
  } catch (const std::exception&) {
    return false;
  }
}

}  // namespace

PinyonShiftApp::PinyonShiftApp(rex::ui::WindowedAppContext& context,
                               std::string_view name,
                               rex::PPCImageInfo config)
    : rex::ReXApp(context, name, config) {
  // Ensure Windows scheduler timer resolution is set to 1ms via timeBeginPeriod(1)
  pinyon_shift::scheduler::InitializeScheduler();
  // The constructing host thread owns the window and the present path.
  // Keep it on the foreground cores at highest priority so background
  // decompression workers can never preempt presentation.
  pinyon_shift::scheduler::PinCurrentThread(
      pinyon_shift::scheduler::ThreadClass::Foreground);
}

std::unique_ptr<rex::ui::WindowedApp> PinyonShiftApp::Create(
    rex::ui::WindowedAppContext& context) {
  if (!pinyon_shift::diagnostics::InitializeEarly()) {
    ExitProcess(ERROR_NOT_SUPPORTED);
  }
  return std::unique_ptr<PinyonShiftApp>(
      new PinyonShiftApp(context, "pinyon_shift", PPCImageConfig));
}

void PinyonShiftApp::OnConfigurePaths(rex::PathConfig& paths) {
  namespace diagnostics = pinyon_shift::diagnostics;
  const auto& state_root = diagnostics::StateRoot();
  if (auto game_root = diagnostics::EnvironmentPath("PINYON_SHIFT_GAME_ROOT")) {
    paths.game_data_root = *game_root;
  }

  if (paths.game_data_root.empty()) {
    const auto exe_dir = diagnostics::ExecutableDirectory();
    std::vector<std::filesystem::path> candidates = {
        exe_dir / ".." / ".." / ".local" / "game" / "base",
        exe_dir / ".." / ".." / ".." / ".local" / "game" / "base",
        exe_dir / ".local" / "game" / "base",
        exe_dir / "game" / "base",
        exe_dir / "game",
        state_root.parent_path() / "game" / "base",
    };

    if (auto local_app_data = diagnostics::EnvironmentPath("LOCALAPPDATA")) {
      candidates.push_back(*local_app_data / "PinyonShift" / "source" / "0.1.1" / ".local" / "game" / "base");
      candidates.push_back(*local_app_data / "PinyonShift" / "game" / "base");
      candidates.push_back(*local_app_data / "PinyonShift" / ".local" / "game" / "base");
      std::error_code ec;
      auto source_dir = *local_app_data / "PinyonShift" / "source";
      if (std::filesystem::is_directory(source_dir, ec)) {
        for (const auto& entry : std::filesystem::directory_iterator(source_dir, ec)) {
          if (entry.is_directory(ec)) {
            candidates.push_back(entry.path() / ".local" / "game" / "base");
          }
        }
      }
    }

    for (const auto& candidate : candidates) {
      std::error_code ec;
      if (std::filesystem::exists(candidate / "default.xex", ec)) {
        paths.game_data_root = std::filesystem::absolute(candidate, ec).lexically_normal();
        diagnostics::RecordEvent("paths.game_root_discovered",
                                 {{"path", paths.game_data_root.string()}});
        break;
      }
    }
  }

  if (paths.game_data_root.empty()) {
    diagnostics::RecordEvent("paths.game_root_missing", {});
    MessageBoxW(
        nullptr,
        L"Pinyon Shift could not find your extracted game files (default.xex).\n\n"
        L"Please launch Pinyon Shift through PinyonShiftLauncher.exe, "
        L"or run tools\\launch-preview.ps1, "
        L"or set the PINYON_SHIFT_GAME_ROOT environment variable to your game folder.",
        L"Game Data Not Found - Pinyon Shift", MB_OK | MB_ICONERROR);
  }
  paths.user_data_root = state_root / "user";
  paths.update_data_root = state_root / "update";
  paths.cache_root = state_root / "cache";
  paths.config_path = state_root / "config" / "pinyon_shift.toml";
  config_path_ = paths.config_path;
  std::error_code write_time_ec;
  last_config_write_time_ =
      std::filesystem::last_write_time(config_path_, write_time_ec);

  bool config_created = false;
  bool config_migrated = false;
  if (!EnsureSupportedConfig(paths.config_path, config_created,
                             config_migrated)) {
    diagnostics::RecordEvent("config.unsupported",
                             {{"path", paths.config_path.string()},
                              {"required_schema", std::to_string(kConfigSchema)}});
    MessageBoxW(nullptr,
                L"Pinyon Shift could not create the host configuration, or its schema is "
                L"unsupported. Remove or migrate pinyon_shift.toml before retrying.",
                L"Unsupported configuration", MB_OK | MB_ICONERROR);
    ExitProcess(ERROR_REVISION_MISMATCH);
  }

  if (REXCVAR_GET(log_file).empty()) {
    REXCVAR_SET(log_file, (state_root / "logs" / "runtime.log").string());
  }

  diagnostics::RecordEvent(
      "paths.configured",
      {{"game", paths.game_data_root.string()},
       {"user", paths.user_data_root.string()},
       {"update", paths.update_data_root.string()},
       {"cache", paths.cache_root.string()},
       {"config", paths.config_path.string()},
       {"config_schema", std::to_string(kConfigSchema)},
       {"config_created", config_created ? "1" : "0"},
       {"config_migrated", config_migrated ? "1" : "0"},
       {"log", REXCVAR_GET(log_file)}});
}

void PinyonShiftApp::OnPostInitLogging() {
  std::string perf_csv = rex::cvar::GetFlagByName("perf_log_csv");
  if (perf_csv.empty() && REXCVAR_GET(pinyon_shift_capture_performance)) {
    perf_csv = (pinyon_shift::diagnostics::StateRoot() / "logs" /
                (pinyon_shift::diagnostics::SessionId() + ".perf.csv"))
                   .string();
  }
  if (!perf_csv.empty()) {
    rex::perf::SetCsvLogPath(perf_csv);
  }
  pinyon_shift::profiling::HitchLogger::Initialize(
      pinyon_shift::diagnostics::StateRoot(),
      pinyon_shift::diagnostics::SessionId());
  pinyon_shift::diagnostics::RecordEvent(
      "logging.ready", {{"config_schema", std::to_string(REXCVAR_GET(pinyon_shift_config_schema))},
                        {"d3d12_tearing_allowed",
                         rex::cvar::GetFlagByName(
                             "d3d12_allow_variable_refresh_rate_and_tearing")},
                        {"vehicle_presentation_stabilization",
                         rex::cvar::GetFlagByName(
                             "pinyon_shift_stabilize_vehicle_presentation")},
                        {"renderer", "d3d12"},
                        {"resolution", rex::cvar::GetFlagByName("resolution")},
                        {"vsync", rex::cvar::GetFlagByName("vsync")},
                        {"draw_resolution_scale_x",
                         rex::cvar::GetFlagByName("draw_resolution_scale_x")},
                        {"draw_resolution_scale_y",
                         rex::cvar::GetFlagByName("draw_resolution_scale_y")},
                        {"anisotropic_override",
                         rex::cvar::GetFlagByName("anisotropic_override")},
                        {"swap_post_effect", rex::cvar::GetFlagByName("swap_post_effect")},
                        {"d3d12_submit_on_primary_buffer_end",
                         rex::cvar::GetFlagByName("d3d12_submit_on_primary_buffer_end")},
                        {"clear_memory_page_state",
                         rex::cvar::GetFlagByName("clear_memory_page_state")},
                        {"perf_csv_enabled", perf_csv.empty() ? "0" : "1"},
                        {"perf_csv", perf_csv},
                        {"hitch_logger_enabled",
                         pinyon_shift::profiling::HitchLogger::IsEnabled() ? "1" : "0"}});
}

void PinyonShiftApp::OnPreSetup(rex::RuntimeConfig& config) {
  // ReXGlue 0.9 separates the Xenos implementation into a runtime-loaded
  // plugin. The CMake helper stages it; this selects it deliberately.
  config.gpu_plugin = "xenos";
  pinyon_shift::diagnostics::RecordEvent(
      "runtime.setup.begin",
      {{"graphics_requested", (config.graphics || !config.gpu_plugin.empty()) ? "1" : "0"},
       {"gpu_plugin", config.gpu_plugin},
       {"audio_requested", config.audio_factory ? "1" : "0"},
       {"input_requested", config.input_factory ? "1" : "0"}});
}

void PinyonShiftApp::OnPostLoadXexImage() {
  const auto title_id = runtime() && runtime()->kernel_state()
                            ? runtime()->kernel_state()->title_id()
                            : 0;
  char title[16]{};
  std::snprintf(title, sizeof(title), "%08X", title_id);
  pinyon_shift::diagnostics::RecordEvent("xex.loaded", {{"title_id", title}});
}

PinyonShiftApp::~PinyonShiftApp() {
  StopConfigMonitorThread();
  // Restore Windows scheduler timer resolution via timeEndPeriod(1)
  pinyon_shift::scheduler::ShutdownScheduler();
}

void PinyonShiftApp::OnPostSetup() {
  pinyon_shift::diagnostics::RefreshCrashReporter();
  QualifyGpuHardware();
  StartConfigMonitorThread();
  StartSchedulerEnforcement();
  pinyon_shift::diagnostics::RecordEvent(
      "runtime.setup.complete",
      {{"memory", runtime() && runtime()->memory() ? "1" : "0"},
       {"vfs", runtime() && runtime()->file_system() ? "1" : "0"},
       {"kernel", runtime() && runtime()->kernel_state() ? "1" : "0"},
       {"graphics", runtime() && runtime()->graphics_system() ? "1" : "0"},
       {"audio", runtime() && runtime()->audio_system() ? "1" : "0"},
       {"input", runtime() && runtime()->input_system() ? "1" : "0"}});
}

void PinyonShiftApp::OnPreLaunchModule() {
  pinyon_shift::diagnostics::RefreshCrashReporter();
  pinyon_shift::diagnostics::RecordEvent("guest.launch.begin");
}

void PinyonShiftApp::OnPostLaunchModule(rex::system::XThread* thread) {
  const std::string thread_id = thread ? std::to_string(thread->thread_id()) : "none";
  ApplyMainGuestThreadPolicy(thread);
  pinyon_shift::diagnostics::RecordEvent("guest.thread.prepared", {{"thread_id", thread_id}});
}

void PinyonShiftApp::OnGuestThreadExit(rex::system::XThread* thread) {
  const std::string thread_id = thread ? std::to_string(thread->thread_id()) : "none";
  pinyon_shift::diagnostics::RecordEvent("guest.thread.exit", {{"thread_id", thread_id}});
}

bool PinyonShiftApp::OnWindowCloseRequested() {
  // ReXGlue 0.9 deliberately hard-exits after accepting a window-close
  // request, so OnDestroy/OnShutdown are not reached on that path. Record the
  // clean qualification boundary before allowing the SDK to terminate.
  StopConfigMonitorThread();
  RecordShutdownOnce();
  return true;
}

void PinyonShiftApp::OnShutdown() {
  StopConfigMonitorThread();
  RecordShutdownOnce();
}

void PinyonShiftApp::RecordShutdownOnce() {
  if (!shutdown_recorded_.exchange(true, std::memory_order_acq_rel)) {
    pinyon_shift::profiling::HitchLogger::Shutdown();
    pinyon_shift::diagnostics::RecordEvent("process.shutdown");
  }
}

void PinyonShiftApp::QualifyGpuHardware() {
  uint32_t vendor_id = 0;
  std::string adapter_name = "Default D3D12 Adapter";

  HMODULE dxgi = LoadLibraryA("dxgi.dll");
  if (dxgi) {
    using CreateDXGIFactory1Fn = HRESULT(WINAPI*)(REFIID, void**);
    auto create_factory = reinterpret_cast<CreateDXGIFactory1Fn>(
        GetProcAddress(dxgi, "CreateDXGIFactory1"));
    if (create_factory) {
      IDXGIFactory1* factory = nullptr;
      if (SUCCEEDED(create_factory(__uuidof(IDXGIFactory1),
                                   reinterpret_cast<void**>(&factory))) &&
          factory) {
        IDXGIAdapter1* adapter = nullptr;
        if (SUCCEEDED(factory->EnumAdapters1(0, &adapter)) && adapter) {
          DXGI_ADAPTER_DESC1 desc{};
          if (SUCCEEDED(adapter->GetDesc1(&desc))) {
            vendor_id = desc.VendorId;
            int size = WideCharToMultiByte(CP_UTF8, 0, desc.Description, -1,
                                           nullptr, 0, nullptr, nullptr);
            if (size > 0) {
              adapter_name.resize(size - 1);
              WideCharToMultiByte(CP_UTF8, 0, desc.Description, -1,
                                  adapter_name.data(), size, nullptr, nullptr);
            }
          }
          adapter->Release();
        }
        factory->Release();
      }
    }
    FreeLibrary(dxgi);
  }

  std::string vendor_str;
  std::string uav_barrier_policy;
  std::string rov_supported = "1";
  if (vendor_id == 0x1002) {
    vendor_str = "AMD";
    uav_barrier_policy = "amd_coherent";
    if (rex::cvar::GetFlagByName("d3d12_submit_on_primary_buffer_end").empty()) {
      rex::cvar::SetFlagByName("d3d12_submit_on_primary_buffer_end", "true");
    }
    if (rex::cvar::GetFlagByName("clear_memory_page_state").empty()) {
      rex::cvar::SetFlagByName("clear_memory_page_state", "false");
    }
    if (rex::cvar::GetFlagByName("d3d12_tiled_shared_memory").empty()) {
      rex::cvar::SetFlagByName("d3d12_tiled_shared_memory", "false");
    }
  } else if (vendor_id == 0x8086) {
    vendor_str = "Intel";
    uav_barrier_policy = "intel_coherent";
    rov_supported = "fallback_supported";
  } else if (vendor_id == 0x10DE) {
    vendor_str = "NVIDIA";
    uav_barrier_policy = "default";
  } else {
    vendor_str = fmt::format("0x{:04X}", vendor_id);
    uav_barrier_policy = "default";
  }

  pinyon_shift::diagnostics::RecordEvent(
      "gpu.qualification.profile",
      {{"vendor_id", fmt::format("0x{:04X}", vendor_id)},
       {"vendor", vendor_str},
       {"adapter", adapter_name},
       {"uav_barrier_policy", uav_barrier_policy},
       {"rov_supported", rov_supported},
       {"live_hotreload_supported", "1"}});
}

void PinyonShiftApp::StartConfigMonitorThread() {
  if (config_path_.empty() || monitor_running_.exchange(true)) {
    return;
  }
  monitor_thread_ = std::make_unique<std::thread>([this]() {
    pinyon_shift::scheduler::PinCurrentThread(
        pinyon_shift::scheduler::ThreadClass::Background);
    while (monitor_running_.load(std::memory_order_relaxed)) {
      std::this_thread::sleep_for(std::chrono::milliseconds(250));
      if (!monitor_running_.load(std::memory_order_relaxed)) {
        break;
      }
      CheckConfigHotReload();
    }
  });
}

void PinyonShiftApp::StopConfigMonitorThread() {
  StopSchedulerEnforcement();
  if (monitor_running_.exchange(false)) {
    if (monitor_thread_ && monitor_thread_->joinable()) {
      monitor_thread_->join();
    }
    monitor_thread_.reset();
  }
}

void PinyonShiftApp::ApplyMainGuestThreadPolicy(
    rex::system::XThread* thread) {
  if (!thread || !thread->thread()) {
    return;
  }
  namespace scheduler = pinyon_shift::scheduler;
  uint64_t foreground = 0;
  uint64_t background = 0;
  const bool affinity_available =
      scheduler::ResolveAffinityMasks(&foreground, &background);
  foreground_affinity_mask_ = affinity_available ? foreground : 0;
  background_affinity_mask_ = affinity_available ? background : 0;
  thread->thread()->set_priority(rex::thread::ThreadPriority::kHighest);
  if (affinity_available) {
    thread->thread()->set_affinity_mask(foreground);
  }
  main_guest_system_id_.store(thread->thread()->system_id(),
                              std::memory_order_release);
  pinyon_shift::diagnostics::RecordEvent(
      "scheduler.main_guest_pinned",
      {{"guest_thread_id", std::to_string(thread->thread_id())},
       {"system_id", std::to_string(thread->thread()->system_id())},
       {"affinity_mask", fmt::format("0x{:X}", foreground)},
       {"priority", "THREAD_PRIORITY_HIGHEST"}});
}

void PinyonShiftApp::StartSchedulerEnforcement() {
  namespace scheduler = pinyon_shift::scheduler;
  uint64_t foreground = 0;
  uint64_t background = 0;
  const bool affinity_available =
      scheduler::ResolveAffinityMasks(&foreground, &background);
  foreground_affinity_mask_ = affinity_available ? foreground : 0;
  background_affinity_mask_ = affinity_available ? background : 0;
  if (scheduler_running_.exchange(true)) {
    return;
  }
  SYSTEM_INFO system_info{};
  GetSystemInfo(&system_info);
  pinyon_shift::diagnostics::RecordEvent(
      "scheduler.ready",
      {{"foreground_mask", fmt::format("0x{:X}", foreground_affinity_mask_)},
       {"background_mask", fmt::format("0x{:X}", background_affinity_mask_)},
       {"affinity_managed", affinity_available ? "1" : "0"},
       {"foreground_priority", "THREAD_PRIORITY_HIGHEST"},
       {"background_priority", "THREAD_PRIORITY_BELOW_NORMAL"},
       {"audio_priority", "THREAD_PRIORITY_NORMAL"},
       {"logical_processors",
        std::to_string(system_info.dwNumberOfProcessors)}});
  scheduler_thread_ = std::make_unique<std::thread>([this]() {
    SchedulerEnforcementLoop();
  });
}

void PinyonShiftApp::StopSchedulerEnforcement() {
  if (scheduler_running_.exchange(false)) {
    if (scheduler_thread_ && scheduler_thread_->joinable()) {
      scheduler_thread_->join();
    }
    scheduler_thread_.reset();
  }
}

void PinyonShiftApp::SchedulerEnforcementLoop() {
  namespace scheduler = pinyon_shift::scheduler;
  // The enforcement pass itself must never disturb the foreground cores.
  scheduler::PinCurrentThread(scheduler::ThreadClass::Background);

  using GetThreadDescriptionFn = HRESULT(WINAPI*)(HANDLE, PWSTR*);
  using CoTaskMemFreeFn = void(WINAPI*)(void*);
  HMODULE kernel32 = GetModuleHandleW(L"kernel32.dll");
  auto get_description = kernel32 ? reinterpret_cast<GetThreadDescriptionFn>(
                                        GetProcAddress(kernel32, "GetThreadDescription"))
                                  : nullptr;
  HMODULE ole32 = LoadLibraryA("ole32.dll");
  auto co_free = ole32 ? reinterpret_cast<CoTaskMemFreeFn>(
                             GetProcAddress(ole32, "CoTaskMemFree"))
                       : nullptr;

  const DWORD process_id = GetCurrentProcessId();
  std::unordered_set<DWORD> classified;
  while (scheduler_running_.load(std::memory_order_relaxed)) {
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    if (!scheduler_running_.load(std::memory_order_relaxed)) {
      break;
    }
    const uint32_t main_guest_id =
        main_guest_system_id_.load(std::memory_order_acquire);
    HANDLE snapshot =
        CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
      continue;
    }
    THREADENTRY32 entry{};
    entry.dwSize = sizeof(entry);
    if (Thread32First(snapshot, &entry)) {
      do {
        if (entry.th32OwnerProcessID != process_id ||
            entry.th32ThreadID == GetCurrentThreadId()) {
          continue;
        }
        const DWORD tid = entry.th32ThreadID;
        if (classified.find(tid) != classified.end()) {
          continue;
        }

        scheduler::ThreadClass thread_class =
            scheduler::ThreadClass::Background;
        bool managed = false;
        if (main_guest_id != 0 && tid == main_guest_id) {
          // The main guest tick keeps foreground even though its
          // SetThreadDescription name also matches the worker prefix.
          thread_class = scheduler::ThreadClass::Foreground;
          managed = true;
          HANDLE thread = OpenThread(THREAD_SET_INFORMATION, FALSE, tid);
          if (thread) {
            if (scheduler::PinThreadHandle(
                    thread, scheduler::ThreadClass::Foreground,
                    foreground_affinity_mask_)) {
              classified.insert(tid);
            }
            CloseHandle(thread);
          }
          continue;
        }

        if (get_description) {
          HANDLE thread = OpenThread(THREAD_SET_INFORMATION |
                                         THREAD_QUERY_INFORMATION,
                                     FALSE, tid);
          if (thread) {
            PWSTR description = nullptr;
            if (SUCCEEDED(get_description(thread, &description))) {
              if (description && *description) {
                managed = scheduler::ClassifyThreadName(description,
                                                        &thread_class);
              }
              if (description && co_free) {
                co_free(description);
              }
            }
            if (managed) {
              const uint64_t mask =
                  thread_class == scheduler::ThreadClass::Foreground
                      ? foreground_affinity_mask_
                      : background_affinity_mask_;
              if (scheduler::PinThreadHandle(thread, thread_class, mask)) {
                classified.insert(tid);
              }
            }
            CloseHandle(thread);
            continue;
          }
        }
      } while (Thread32Next(snapshot, &entry));
    }
    CloseHandle(snapshot);
    if (classified.size() > 1024) {
      classified.clear();
    }
  }
  if (ole32) {
    FreeLibrary(ole32);
  }
}

void PinyonShiftApp::CheckConfigHotReload() {
  std::error_code ec;
  if (!std::filesystem::exists(config_path_, ec)) {
    return;
  }
  const auto current_write_time =
      std::filesystem::last_write_time(config_path_, ec);
  if (ec || current_write_time == last_config_write_time_) {
    return;
  }
  last_config_write_time_ = current_write_time;

  std::ifstream input(config_path_, std::ios::binary);
  if (!input) {
    return;
  }
  std::ostringstream contents;
  contents << input.rdbuf();
  input.close();
  const std::string text = contents.str();

  auto get_val = [&](const std::string& name, const std::string& def) -> std::string {
    std::regex pattern("(?:^|\\n)\\s*" + name + "\\s*=\\s*([^#\\r\\n]+)");
    std::smatch m;
    if (std::regex_search(text, m, pattern) && m.size() > 1) {
      std::string val = m[1].str();
      while (!val.empty() && (val.front() == ' ' || val.front() == '\"')) val.erase(0, 1);
      while (!val.empty() && (val.back() == ' ' || val.back() == '\"' || val.back() == '\r')) val.pop_back();
      return val;
    }
    return def;
  };

  const std::string res_x = get_val("draw_resolution_scale_x", "1");
  const std::string res_y = get_val("draw_resolution_scale_y", "1");
  const std::string aniso = get_val("anisotropic_override", "2");
  const std::string post_fx = get_val("swap_post_effect", "none");
  const std::string submit_primary = get_val("d3d12_submit_on_primary_buffer_end", "true");
  const std::string clear_page = get_val("clear_memory_page_state", "false");

  bool changed = false;
  auto update_flag = [&](const char* name, const std::string& new_val) {
    std::string cur = rex::cvar::GetFlagByName(name);
    if (cur != new_val && !new_val.empty()) {
      rex::cvar::SetFlagByName(name, new_val);
      changed = true;
    }
  };

  update_flag("draw_resolution_scale_x", res_x);
  update_flag("draw_resolution_scale_y", res_y);
  update_flag("anisotropic_override", aniso);
  update_flag("swap_post_effect", post_fx);
  update_flag("d3d12_submit_on_primary_buffer_end", submit_primary);
  update_flag("clear_memory_page_state", clear_page);

  if (changed) {
    pinyon_shift::diagnostics::RecordEvent(
        "graphics.hotreload.applied",
        {{"draw_resolution_scale_x", res_x},
         {"draw_resolution_scale_y", res_y},
         {"anisotropic_override", aniso},
         {"swap_post_effect", post_fx}});
  }
}

