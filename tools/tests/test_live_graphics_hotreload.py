import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/set-graphics-experiment.ps1"
POWERSHELL = shutil.which("powershell")


@unittest.skipUnless(POWERSHELL, "Windows PowerShell is required")
class LiveGraphicsHotReloadTests(unittest.TestCase):
    def run_tool(self, state, *arguments):
        completed = subprocess.run(
            [POWERSHELL, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(TOOL), "-StateRoot", str(state), *arguments, "-Json"],
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_live_apply_sets_restart_required_false(self):
        with tempfile.TemporaryDirectory(prefix="pinyon-live-") as temporary:
            state = pathlib.Path(temporary)
            config = state / "config/pinyon_shift.toml"
            config.parent.mkdir(parents=True)
            config.write_text("pinyon_shift_config_schema = 4\n", encoding="utf-8")

            # Standard Apply requires restart
            standard = self.run_tool(
                state, "-Action", "Apply", "-Anisotropy", "16",
                "-PostEffect", "fxaa", "-ResolutionScale", "2",
            )
            self.assertTrue(standard["restart_required"])
            self.assertEqual(standard["settings"]["resolution_scale"], 2)

            # Live Apply does not require restart
            live = self.run_tool(
                state, "-Action", "Apply", "-Anisotropy", "8",
                "-PostEffect", "fxaa_extreme", "-ResolutionScale", "1", "-Live",
            )
            self.assertFalse(live["restart_required"])
            self.assertEqual(live["settings"]["resolution_scale"], 1)
            self.assertEqual(live["settings"]["anisotropy"], 8)
            self.assertEqual(live["settings"]["post_effect"], "fxaa_extreme")

    def test_live_reset_and_restore_report_no_restart_when_live(self):
        with tempfile.TemporaryDirectory(prefix="pinyon-live-") as temporary:
            state = pathlib.Path(temporary)
            config = state / "config/pinyon_shift.toml"
            config.parent.mkdir(parents=True)
            config.write_text("pinyon_shift_config_schema = 4\nswap_post_effect = \"fxaa\"\n", encoding="utf-8")

            reset = self.run_tool(state, "-Action", "Reset", "-Live")
            self.assertFalse(reset["restart_required"])
            self.assertEqual(reset["settings"]["post_effect"], "none")

            restore = self.run_tool(state, "-Action", "Restore", "-Live")
            self.assertFalse(restore["restart_required"])
            self.assertEqual(restore["settings"]["post_effect"], "fxaa")

    def test_adaptive_vendor_uav_barrier_patch_contract(self):
        patch = (ROOT / "patches/rexglue/0038-m4-adaptive-vendor-uav-barriers.patch").read_text(
            encoding="utf-8"
        )
        self.assertIn("diff --git a/src/graphics/d3d12/command_processor.cpp", patch)
        self.assertIn("0x1002 /* AMD */", patch)
        self.assertIn("0x8086 /* Intel */", patch)
        self.assertIn("PushUAVBarrier", patch)
        self.assertIn("SubmitBarriers", patch)

    def test_runtime_app_registers_live_hotreload_and_gpu_qualification(self):
        app = (ROOT / "src/pinyon_shift_app.cpp").read_text(encoding="utf-8")
        self.assertIn("QualifyGpuHardware()", app)
        self.assertIn("StartConfigMonitorThread()", app)
        self.assertIn("StopConfigMonitorThread()", app)
        self.assertIn("CheckConfigHotReload()", app)
        self.assertIn("gpu.qualification.profile", app)
        self.assertIn("graphics.hotreload.applied", app)
        self.assertIn("amd_coherent", app)
        self.assertIn("intel_coherent", app)
        self.assertIn("live_hotreload_supported", app)


if __name__ == "__main__":
    unittest.main()
