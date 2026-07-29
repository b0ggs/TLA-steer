import unittest

from src.tags import merge_tags


class MergeTagsRegressionTests(unittest.TestCase):
    def test_default_accumulator_does_not_leak_between_calls(self):
        self.assertEqual(["alpha"], merge_tags(["alpha"]))
        self.assertEqual(["beta"], merge_tags(["beta"]))


if __name__ == "__main__":
    unittest.main()
