#pragma once

#include <atomic>
#include <cstdint>
#include <memory>

#include <rex/rex_app.h>

class PinyonShiftApp final : public rex::ReXApp {
 public:
  PinyonShiftApp(rex::ui::WindowedAppContext& context,
                 std::string_view name,
                 rex::PPCImageInfo config);

  ~PinyonShiftApp() override;

  static std::unique_ptr<rex::ui::WindowedApp> Create(
      rex::ui::WindowedAppContext& context);

 protected:
  void OnConfigurePaths(rex::PathConfig& paths) override;
  void OnPostInitLogging() override;
  void OnPreSetup(rex::RuntimeConfig& config) override;
  void OnPostLoadXexImage() override;
  void OnPostSetup() override;
  void OnPreLaunchModule() override;
  void OnPostLaunchModule(rex::system::XThread* thread) override;
  void OnGuestThreadExit(rex::system::XThread* thread) override;
  bool OnWindowCloseRequested() override;
  void OnShutdown() override;

 private:
  void RecordShutdownOnce();
  void CheckConfigHotReload();
  void StartConfigMonitorThread();
  void StopConfigMonitorThread();
  void QualifyGpuHardware();
  void StartSchedulerEnforcement();
  void StopSchedulerEnforcement();
  void SchedulerEnforcementLoop();
  void ApplyMainGuestThreadPolicy(rex::system::XThread* thread);

  std::atomic_bool shutdown_recorded_{false};
  std::filesystem::path config_path_;
  std::filesystem::file_time_type last_config_write_time_{};
  std::atomic_bool monitor_running_{false};
  std::unique_ptr<std::thread> monitor_thread_;
  std::atomic_bool scheduler_running_{false};
  std::unique_ptr<std::thread> scheduler_thread_;
  std::atomic_uint32_t main_guest_system_id_{0};
  uint64_t foreground_affinity_mask_{0};
  uint64_t background_affinity_mask_{0};
};
