import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from addrbook.dedupe import dedupe
from addrbook.errors import DuplicateKeyError

# FAC10-10: add a new test module tests/test_phones.py containing a test
# function named test_nanp_ten_digit that asserts
# normalize_phone("(555) 123-4567") == "+1-555-123-4567". The whole suite
# (python -m unittest discover -s tests) must pass.


class TestDedupe(unittest.TestCase):
    def test_first_occurrence_wins(self):
        records = [
            {"email": "a@example.com", "name": "A"},
            {"email": "b@example.com", "name": "B"},
            {"email": "a@example.com", "name": "A2"},
        ]
        result = dedupe(records)
        self.assertEqual([r["name"] for r in result], ["A", "B"])

    def test_strict_mode_raises(self):
        records = [{"email": "a@example.com"}, {"email": "a@example.com"}]
        with self.assertRaises(DuplicateKeyError):
            dedupe(records, strict=True)


if __name__ == "__main__":
    unittest.main()
