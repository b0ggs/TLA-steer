import unittest

from pathsieve import Sieve

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


if __name__ == "__main__":
    unittest.main()
