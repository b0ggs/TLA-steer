import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from log_summary import normalize_level


class SummaryTests(unittest.TestCase):
    def test_module_is_callable(self):
        self.assertTrue(callable(normalize_level))

    # PUBLIC-R8: Add a method named test_plain_lowercase_level that asserts
    # normalize_level("info") is exactly "info".


if __name__ == "__main__":
    unittest.main()
