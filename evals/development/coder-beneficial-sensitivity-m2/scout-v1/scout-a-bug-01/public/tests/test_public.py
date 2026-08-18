import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from headers import get_header


class HeaderTests(unittest.TestCase):
    def test_module_is_callable(self):
        self.assertTrue(callable(get_header))

    # PUBLIC-R8: Add a method named test_exact_case_lookup that asserts an
    # existing exact-case key is returned by get_header.


if __name__ == "__main__":
    unittest.main()
