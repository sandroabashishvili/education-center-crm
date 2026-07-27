import sys
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = APP_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from utils import normalize_text, parse_float, parse_int, parse_page


class UtilsTests(unittest.TestCase):
    def test_normalize_text_strips_whitespace(self):
        self.assertEqual(normalize_text("  Alice  "), "Alice")
        self.assertEqual(normalize_text(None), "")

    def test_parse_page_falls_back_to_default(self):
        self.assertEqual(parse_page("abc", default=1), 1)
        self.assertEqual(parse_page("3", default=1), 3)

    def test_safe_numeric_parsing(self):
        self.assertEqual(parse_int("12"), 12)
        self.assertIsNone(parse_int("invalid"))
        self.assertEqual(parse_float("12.50"), 12.5)
        self.assertEqual(parse_float("invalid"), 0.0)


if __name__ == "__main__":
    unittest.main()
