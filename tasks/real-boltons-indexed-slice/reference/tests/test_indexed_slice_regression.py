import unittest

from boltons.setutils import IndexedSet


class IndexedSetSliceRegressionTests(unittest.TestCase):
    def test_slice_bounds_after_removal(self):
        values = IndexedSet(range(10))
        values.pop(2)
        self.assertEqual(list(values[1:4]), [1, 3, 4])
        self.assertEqual(list(values[-3:]), [7, 8, 9])
        self.assertEqual(list(values[2:-1]), [3, 4, 5, 6, 7, 8])
        self.assertIsInstance(values[1:4], IndexedSet)

    def test_positive_step_matches_list(self):
        values = IndexedSet(range(10))
        for value in (0, 3, 6, 9):
            values.discard(value)
        expected = list(values)
        for slice_value in (slice(None), slice(1, 5), slice(-5, -1), slice(0, 7, 2)):
            with self.subTest(slice_value=slice_value):
                self.assertEqual(list(values[slice_value]), expected[slice_value])


if __name__ == "__main__":
    unittest.main()

