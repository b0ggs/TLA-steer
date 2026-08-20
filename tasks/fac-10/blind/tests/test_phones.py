import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from addrbook.phones import normalize_phone


class TestPhones(unittest.TestCase):
    def test_nanp_ten_digit(self):
        self.assertEqual(
            normalize_phone("(555) 123-4567"), "+1-555-123-4567"
        )

    def test_nanp_leading_country_code(self):
        self.assertEqual(
            normalize_phone("1 (555) 010-9999"), "+1-555-010-9999"
        )

    def test_non_nanp_remains_digits_only(self):
        self.assertEqual(normalize_phone("+44 (0)20 1234"), "440201234")


if __name__ == "__main__":
    unittest.main()
