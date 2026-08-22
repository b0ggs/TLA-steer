from pathlib import Path
import unittest

import tomli


DATA = Path(__file__).with_name("data")


class ExplicitTableBehavior(unittest.TestCase):
    def test_explicit_table_cases_from_upstream_fix(self):
        names = (
            "extend-defined-table.toml",
            "extend-defined-table-with-subtable.toml",
        )
        for name in names:
            with self.subTest(name=name):
                source = (DATA / name).read_text(encoding="utf-8")
                with self.assertRaises(tomli.TOMLDecodeError):
                    tomli.loads(source)


class ArrayOfTablesBehavior(unittest.TestCase):
    def test_array_of_tables_case_from_upstream_fix(self):
        source = (DATA / "extend-defined-aot.toml").read_text(encoding="utf-8")
        with self.assertRaises(tomli.TOMLDecodeError):
            tomli.loads(source)


class ExistingBehaviorRegression(unittest.TestCase):
    def test_unrelated_dotted_key_remains_valid(self):
        source = "[a.b.c]\nz = 9\n[a]\nother.t = 8\n"
        self.assertEqual(
            tomli.loads(source),
            {"a": {"b": {"c": {"z": 9}}, "other": {"t": 8}}},
        )


if __name__ == "__main__":
    unittest.main()

