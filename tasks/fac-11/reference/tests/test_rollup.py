import unittest

from pulsemetrics.rollup import rollup


class RollupTests(unittest.TestCase):
    def test_counts_and_extremes(self):
        samples = [
            {"metric": "cpu", "value": 1.0},
            {"metric": "cpu", "value": 3.0},
            {"metric": "mem", "value": 2.0},
        ]
        result = rollup(samples)
        self.assertEqual(result["cpu"]["count"], 2)
        self.assertEqual(result["cpu"]["min"], 1.0)
        self.assertEqual(result["cpu"]["max"], 3.0)
        self.assertEqual(result["mem"]["count"], 1)

    def test_unweighted_mean(self):
        samples = [{"metric": "cpu", "value": v} for v in (10.0, 20.0, 30.0)]
        self.assertAlmostEqual(rollup(samples)["cpu"]["mean"], 20.0)

    def test_weighted_mean(self):
        samples = [
            {"metric": "cpu", "value": 10.0, "weight": 1.0},
            {"metric": "cpu", "value": 20.0, "weight": 3.0},
        ]
        result = rollup(samples)
        self.assertAlmostEqual(result["cpu"]["mean"], 17.5)
        self.assertAlmostEqual(result["cpu"]["weight_total"], 4.0)


if __name__ == "__main__":
    unittest.main()
