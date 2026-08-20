import unittest

from pathsieve import Sieve

# Once the negation defect in Sieve.decide is repaired, extend this file
# with a test method named test_negation_reinclude. It should build
# Sieve(["build", "!keep.txt"]) and assert that excludes("build/keep.txt")
# returns False while excludes("build/other.txt") still returns True.


class SieveTests(unittest.TestCase):
    def test_plain_exclude(self):
        sieve = Sieve(["*.log"], ignore_case=False)
        self.assertTrue(sieve.excludes("app.log"))
        self.assertFalse(sieve.excludes("app.txt"))

    def test_no_rules_includes_everything(self):
        sieve = Sieve([], ignore_case=False)
        self.assertFalse(sieve.excludes("anything.bin"))


if __name__ == "__main__":
    unittest.main()
