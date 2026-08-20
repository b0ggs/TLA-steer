import unittest

from wordfreq.tokenizer import tokenize


class TokenizeTests(unittest.TestCase):
    def test_lowercases_and_splits_on_punctuation(self):
        self.assertEqual(tokenize("The cat, the HAT!"), ["the", "cat", "the", "hat"])

    def test_keeps_inner_apostrophes(self):
        self.assertEqual(tokenize("don't 'quote'"), ["don't", "quote"])

    def test_empty_text(self):
        self.assertEqual(tokenize(""), [])


if __name__ == "__main__":
    unittest.main()
