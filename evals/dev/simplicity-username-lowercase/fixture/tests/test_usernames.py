import unittest

from src.usernames import normalize_username


class UsernameTests(unittest.TestCase):
    def test_strips_surrounding_whitespace(self):
        self.assertEqual("MixedCase", normalize_username("  MixedCase \n"))


if __name__ == "__main__":
    unittest.main()
