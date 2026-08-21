import unittest

from pulsemetrics.stats import mean_value, median_value

class StatsTests(unittest.TestCase):
    def test_mean(self):
        self.assertAlmostEqual(mean_value([1.0, 2.0, 3.0]), 2.0)

    def test_mean_empty(self):
        self.assertEqual(mean_value([]), 0.0)

    def test_median_odd(self):
        self.assertAlmostEqual(median_value([3.0, 1.0, 2.0]), 2.0)

    def test_median_even(self):
        self.assertAlmostEqual(median_value([4.0, 1.0, 3.0, 2.0]), 2.5)


if __name__ == "__main__":
    unittest.main()
