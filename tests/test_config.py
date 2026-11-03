import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config as cfgmod  # noqa: E402


class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.addCleanup(self.d.cleanup)
        old = os.environ.get("APPDATA")
        os.environ["APPDATA"] = self.d.name
        self.addCleanup(lambda: os.environ.__setitem__("APPDATA", old) if old is not None
                        else os.environ.pop("APPDATA", None))
        self.dir = Path(self.d.name) / "ClipboardFlash"
        self.dir.mkdir()

    def test_bom_and_non_ascii(self):
        (self.dir / "config.json").write_bytes(
            b'\xef\xbb\xbf{"popup_bg_color": "#fff", "note": "caf\xc3\xa9"}')
        c = cfgmod.Config()
        self.assertEqual(c.get("popup_bg_color"), "#fff")
        self.assertEqual(c.get("note"), "café")
        self.assertEqual(c.get("popup_duration"), 1000)

    def test_non_object_ignored(self):
        (self.dir / "config.json").write_text("[1, 2]")
        self.assertEqual(cfgmod.Config().get("popup_duration"), 1000)

    def test_save_roundtrip_atomic(self):
        c = cfgmod.Config()
        c.set("note", "ü")
        c.save()
        self.assertEqual(cfgmod.Config().get("note"), "ü")
        self.assertEqual(os.listdir(self.dir), ["config.json"])

    def test_reset(self):
        c = cfgmod.Config()
        c.set("popup_duration", 5)
        c.reset_to_defaults()
        self.assertEqual(cfgmod.Config().get("popup_duration"), 1000)


if __name__ == "__main__":
    unittest.main()
