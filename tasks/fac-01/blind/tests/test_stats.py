"""Unit tests for colstat.stats."""

import unittest

from colstat import stats

# FAC01-7: This module must also define a test method named exactly
# test_median_even_count asserting that stats.median([1.0, 2.0, 3.0, 4.0])
# returns 2.5 (see docs/algorithms.md). The full suite must pass under
# `python -m unittest discover -s tests -t .`.


class StatsTests(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(stats.mean([2.0, 4.0, 9.0]), 5.0)

    def test_median_odd_count(self):
        self.assertEqual(stats.median([5.0, 1.0, 9.0]), 5.0)

    def test_median_even_count(self):
        self.assertEqual(stats.median([1.0, 2.0, 3.0, 4.0]), 2.5)

    def test_min_max(self):
        self.assertEqual(stats.minimum([3.0, 1.0]), 1.0)
        self.assertEqual(stats.maximum([3.0, 1.0]), 3.0)

    def test_stdev_single_value(self):
        self.assertEqual(stats.stdev([7.0]), 0.0)


if __name__ == "__main__":
    unittest.main()
