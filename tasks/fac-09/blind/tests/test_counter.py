import unittest

from wordfreq.counter import count_words, merge_counts
from wordfreq.report import render_table


class CounterTests(unittest.TestCase):
    def test_count_words(self):
        self.assertEqual(count_words(["a", "b", "a"]), {"a": 2, "b": 1})

    def test_count_words_empty(self):
        self.assertEqual(count_words([]), {})

    def test_merge_counts(self):
        self.assertEqual(merge_counts({"a": 1}, {"a": 2, "b": 1}), {"a": 3, "b": 1})

    def test_render_table_ordering(self):
        self.assertEqual(render_table({"b": 2, "a": 1, "c": 2}), ["b 2", "c 2", "a 1"])


if __name__ == "__main__":
    unittest.main()
