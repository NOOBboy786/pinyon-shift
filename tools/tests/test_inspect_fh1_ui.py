import importlib.util
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "inspect_fh1_ui", ROOT / "tools" / "inspect-fh1-ui.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class InspectFh1UiTests(unittest.TestCase):
    def test_resolves_local_header_and_payload_offsets(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "ui.zip"
            with ZipFile(archive, "w") as zipped:
                zipped.writestr("Scenes/ui4/925_PAUSE_MENU.bgf", b"payload")
            with ZipFile(archive) as zipped:
                info = zipped.getinfo("Scenes/ui4/925_PAUSE_MENU.bgf")
            resolved = MODULE.payload_offset(archive, info.header_offset, "auto")
            self.assertEqual(b"payload", MODULE._read_range(archive, resolved, 7))
            self.assertEqual(resolved, MODULE.payload_offset(archive, resolved, "auto"))

    def test_rejects_truncated_payload_range(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "ui.zip"
            archive.write_bytes(b"short")
            with self.assertRaises(MODULE.UiInspectionError):
                MODULE._read_range(archive, 4, 2)

    def test_catalogs_entries_font_aliases_and_asset_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / ".local" / "game"
            media = game / "media"
            media.mkdir(parents=True)
            archive = media / "UI.zip"
            fontmap = b'<fontmap><mapping fontname="Horizon_A" target="A" /></fontmap>'
            scene = b"AnarkBGF GAME:\\Media\\UI\\Textures\\UI4\\Common\\Tick.xds"
            with ZipFile(archive, "w") as zipped:
                zipped.writestr("fontmap.xml", fontmap)
                zipped.writestr("Scenes/ui4/925_PAUSE_MENU.bgf", scene)
            output = root / ".local" / "ui" / "catalog.json"
            result = MODULE.inspect(
                game,
                output,
                [archive],
                patterns=["Scenes/ui4/*.bgf"],
            )
            entries = result["archives"][0]["entries"]
            pause = next(item for item in entries if item["scene_family"] == "925_PAUSE_MENU")
            self.assertTrue(pause["extracted"])
            self.assertIn("GAME:\\Media\\UI\\Textures\\UI4\\Common\\Tick.xds", pause["asset_references"])
            self.assertEqual("A", result["fontmap"]["mappings"][0]["target"])
            self.assertEqual(zlib.crc32(scene) & 0xFFFFFFFF, int(pause["crc32"], 16))
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
