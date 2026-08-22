import unittest

from boltons.setutils import IndexedSet


class IndexedSetSliceRegressionTests(unittest.TestCase):

    def setUp(self):
        self.indexed = IndexedSet(range(10))
        self.indexed.remove(2)
        self.contents = list(self.indexed)

    def assert_matches_list_slice(self, requested_slice):
        result = self.indexed[requested_slice]

        self.assertIsInstance(result, IndexedSet)
        self.assertEqual(list(result), self.contents[requested_slice])

    def test_positive_bounds_after_removal(self):
        for requested_slice in (
                slice(2, 6),
                slice(1, 8, 2),
                slice(3, None, 3),
                slice(None, 5),
        ):
            with self.subTest(requested_slice=requested_slice):
                self.assert_matches_list_slice(requested_slice)

    def test_negative_bounds_after_removal(self):
        for requested_slice in (
                slice(-7, -2),
                slice(-8, -1, 2),
                slice(None, -3),
                slice(-4, None),
                slice(-20, 20),
        ):
            with self.subTest(requested_slice=requested_slice):
                self.assert_matches_list_slice(requested_slice)


if __name__ == '__main__':
    unittest.main()
