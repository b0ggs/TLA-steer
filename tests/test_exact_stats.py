import unittest

from mdseval.exact_stats import ExactProbability, is_at_or_below, one_sided_sign_test


class ExactStatsTests(unittest.TestCase):
    def test_probability_is_canonical_exact_and_validated(self) -> None:
        probability = ExactProbability(14, 64)
        self.assertEqual(probability, ExactProbability(7, 32))
        self.assertEqual((probability.numerator, probability.denominator), (7, 32))
        self.assertEqual(float(probability), 7 / 32)
        self.assertTrue(is_at_or_below(ExactProbability(1, 32), ExactProbability(1, 20)))
        self.assertFalse(is_at_or_below(ExactProbability(1, 16), ExactProbability(1, 20)))
        for values, error in (
            ((True, 2), TypeError),
            ((1.0, 2), TypeError),
            ((-1, 2), ValueError),
            ((3, 2), ValueError),
            ((0, 0), ValueError),
        ):
            with self.subTest(values=values), self.assertRaises(error):
                ExactProbability(*values)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            is_at_or_below(0.05, ExactProbability(1, 20))  # type: ignore[arg-type]

    def test_one_sided_fair_coin_upper_tails_are_exact(self) -> None:
        expected = {
            (6, 0): (1, 64),
            (5, 0): (1, 32),
            (5, 1): (7, 64),
            (4, 0): (1, 16),
            (0, 0): (1, 1),
        }
        for counts, fraction in expected.items():
            with self.subTest(counts=counts):
                probability = one_sided_sign_test(*counts)
                self.assertEqual(
                    (probability.numerator, probability.denominator), fraction
                )
        for counts, error in (
            ((-1, 0), ValueError),
            ((0, -1), ValueError),
            ((True, 0), TypeError),
            ((1.0, 0), TypeError),
        ):
            with self.subTest(counts=counts), self.assertRaises(error):
                one_sided_sign_test(*counts)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
