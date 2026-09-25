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
class GraphicsSettingsTests(unittest.TestCase):
    def run_tool(self, state, *arguments):
        completed = subprocess.run(
            [POWERSHELL, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-File", str(TOOL), "-StateRoot", str(state), *arguments, "-Json"],
            capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_apply_migrates_schema_and_restore_recovers_previous_file(self):
        with tempfile.TemporaryDirectory(prefix="pinyon-settings-") as temporary:
            state = pathlib.Path(temporary)
            config = state / "config/pinyon_shift.toml"
            config.parent.mkdir(parents=True)
            original = "pinyon_shift_config_schema = 1\nmnk_mode = true\ncustom_value = 77\n"
            config.write_text(original, encoding="utf-8")
            result = self.run_tool(
                state, "-Action", "Apply", "-Anisotropy", "16",
                "-PostEffect", "fxaa", "-ResolutionScale", "2",
            )
            updated = config.read_text(encoding="utf-8")
            self.assertEqual(result["settings"]["anisotropy"], 16)
            self.assertIn("pinyon_shift_config_schema = 4", updated)
            self.assertIn("custom_value = 77", updated)
            self.assertIn("draw_resolution_scale_x = 2", updated)
            self.assertTrue(pathlib.Path(result["backup_path"]).is_file())
            self.run_tool(state, "-Action", "Restore")
            self.assertEqual(config.read_text(encoding="utf-8"), original)

    def test_reset_writes_supported_defaults_and_preserves_backup(self):
        with tempfile.TemporaryDirectory(prefix="pinyon-settings-") as temporary:
            state = pathlib.Path(temporary)
            config = state / "config/pinyon_shift.toml"
            config.parent.mkdir(parents=True)
            config.write_text("pinyon_shift_config_schema = 4\nswap_post_effect = \"fxaa\"\n", encoding="utf-8")
            result = self.run_tool(state, "-Action", "Reset")
            text = config.read_text(encoding="utf-8")
            self.assertIn("swap_post_effect = \"none\"", text)
            self.assertIn("draw_resolution_scale_x = 1", text)
            self.assertIn("resolution = \"720p\"", text)
            self.assertIn("d3d12_submit_on_primary_buffer_end = false", text)
            self.assertIn("clear_memory_page_state = false", text)
            self.assertTrue(pathlib.Path(result["backup_path"]).is_file())

    def test_apply_performance_preset_and_anisotropy_levels(self):
        with tempfile.TemporaryDirectory(prefix="pinyon-settings-") as temporary:
            state = pathlib.Path(temporary)
            config = state / "config/pinyon_shift.toml"
            config.parent.mkdir(parents=True)
            config.write_text("pinyon_shift_config_schema = 4\n", encoding="utf-8")
            result = self.run_tool(state, "-Action", "Apply", "-Preset", "performance_30fps")
            text = config.read_text(encoding="utf-8")
            self.assertEqual(result["settings"]["preset"], "performance_30fps")
            self.assertEqual(result["settings"]["resolution"], "720p")
            self.assertEqual(result["settings"]["anisotropy"], 2)
            self.assertEqual(result["settings"]["post_effect"], "none")
            self.assertEqual(result["settings"]["resolution_scale"], 1)
            self.assertIn("anisotropic_override = 2", text)
            self.assertIn("resolution = \"720p\"", text)
            self.assertIn("d3d12_submit_on_primary_buffer_end = false", text)
            self.assertIn("clear_memory_page_state = false", text)

            # Test 1x anisotropy
            aniso1 = self.run_tool(state, "-Action", "Apply", "-Anisotropy", "1")
            self.assertEqual(aniso1["settings"]["anisotropy"], 1)
            self.assertIn("anisotropic_override = 1", config.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
