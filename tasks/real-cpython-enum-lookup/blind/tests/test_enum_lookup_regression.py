import importlib.util
from pathlib import Path
import unittest


ENUM_PATH = Path(__file__).resolve().parents[1] / "enum.py"
ENUM_SPEC = importlib.util.spec_from_file_location("enum_under_test", ENUM_PATH)
enum_under_test = importlib.util.module_from_spec(ENUM_SPEC)
ENUM_SPEC.loader.exec_module(enum_under_test)
Enum = enum_under_test.Enum


class Directions(Enum):
    DOWN_ONLY = frozenset({"sc"})


class EnumLookupRegressionTests(unittest.TestCase):
    def test_unhashable_value_matches_hashable_member_value(self):
        self.assertIs(Directions({"sc"}), Directions.DOWN_ONLY)


if __name__ == "__main__":
    unittest.main()
