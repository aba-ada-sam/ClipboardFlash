import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from winutil import ps_quote, shortcut_script  # noqa: E402


class PsQuoteTest(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(ps_quote("C:\\a b\\c"), "'C:\\a b\\c'")

    def test_apostrophe_cannot_break_out(self):
        q = ps_quote("C:\\Users\\O'Brien'; calc; '")
        self.assertEqual(q, "'C:\\Users\\O''Brien''; calc; '''")
        # every inner quote is doubled, so the literal only ends at the final quote
        inner = q[1:-1].replace("''", "")
        self.assertNotIn("'", inner)

    def test_shortcut_script_quotes_every_field(self):
        s = shortcut_script("C:\\S\\O'B.lnk", "C:\\py'w.exe", '"x\'y"', "D:\\w'd")
        for frag in ("'C:\\S\\O''B.lnk'", "'C:\\py''w.exe'", "'\"x''y\"'", "'D:\\w''d'"):
            self.assertIn(frag, s)


if __name__ == "__main__":
    unittest.main()
