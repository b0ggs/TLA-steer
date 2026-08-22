import unittest

from boltons.setutils import IndexedSet


class RemovedBoundsBehavior(unittest.TestCase):
    def test_upstream_reported_bounds(self):
        values = IndexedSet(range(10))
        values.pop(2)
        self.assertEqual(list(values), [0, 1, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(list(values[1:4]), [1, 3, 4])
        self.assertEqual(list(values[-3:]), [7, 8, 9])
        self.assertEqual(list(values[2:-1]), [3, 4, 5, 6, 7, 8])
        self.assertIsInstance(values[1:4], IndexedSet)


class SliceAgreementBehavior(unittest.TestCase):
    def test_positive_steps_match_current_contents(self):
        bounds = (None, -12, -9, -5, -1, 0, 1, 4, 8, 9, 12)
        steps = (None, 1, 2, 3)
        removal_patterns = (
            (),
            (2,),
            (0, 1, 2),
            (7, 8, 9),
            (0, 3, 6, 9),
            (1, 2, 5, 6),
        )
        for removals in removal_patterns:
            values = IndexedSet(range(10))
            for value in removals:
                values.discard(value)
            current = list(values)
            for start in bounds:
                for stop in bounds:
                    for step in steps:
                        slice_value = slice(start, stop, step)
                        with self.subTest(removals=removals, slice_value=slice_value):
                            result = values[slice_value]
                            self.assertIsInstance(result, IndexedSet)
                            self.assertEqual(list(result), current[slice_value])


class ExistingBehaviorRegression(unittest.TestCase):
    def test_slicing_without_removals_is_unchanged(self):
        values = IndexedSet(range(6))
        self.assertEqual(list(values[1:4]), [1, 2, 3])
        self.assertEqual(list(values[-2:]), [4, 5])
        self.assertEqual(values[2], 2)


if __name__ == "__main__":
    unittest.main()

