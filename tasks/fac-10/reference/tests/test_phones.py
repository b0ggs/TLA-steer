import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from addrbook.phones import normalize_phone


class TestPhones(unittest.TestCase):
    def test_nanp_ten_digit(self):
        self.assertEqual(normalize_phone("(555) 123-4567"), "+1-555-123-4567")

    def test_nanp_eleven_digit_leading_one(self):
        self.assertEqual(normalize_phone("1 (555) 010-9999"), "+1-555-010-9999")

    def test_non_nanp_falls_back_to_digits(self):
        self.assertEqual(normalize_phone("+44 20 7946 0958"), "442079460958")


if __name__ == "__main__":
    unittest.main()
