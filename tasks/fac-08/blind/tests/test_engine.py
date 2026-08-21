import unittest

from pathsieve import PatternError, Sieve, filter_paths


class SieveTests(unittest.TestCase):
    def test_plain_exclude(self):
        sieve = Sieve(["*.log"], ignore_case=False)
        self.assertTrue(sieve.excludes("app.log"))
        self.assertFalse(sieve.excludes("app.txt"))

    def test_no_rules_includes_everything(self):
        sieve = Sieve([], ignore_case=False)
        self.assertFalse(sieve.excludes("anything.bin"))

    def test_negation_reinclude(self):
        sieve = Sieve(["build", "!keep.txt"])
        self.assertFalse(sieve.excludes("build/keep.txt"))
        self.assertTrue(sieve.excludes("build/other.txt"))

    def test_later_exclusion_overrides_negation(self):
        sieve = Sieve(["*.log", "!debug.log", "debug.log"])
        self.assertTrue(sieve.excludes("debug.log"))

    def test_matching_is_case_sensitive_by_default(self):
        self.assertFalse(Sieve(["*.PY"]).excludes("main.py"))
        self.assertTrue(Sieve(["*.PY"], ignore_case=True).excludes("main.py"))

    def test_filter_paths_preserves_input_order(self):
        paths = ["zeta.txt", "app.log", "alpha.txt"]
        self.assertEqual(
            filter_paths(paths, ["*.log"]), ["zeta.txt", "alpha.txt"]
        )

    def test_pattern_error_is_public(self):
        self.assertTrue(issubclass(PatternError, ValueError))


if __name__ == "__main__":
    unittest.main()
