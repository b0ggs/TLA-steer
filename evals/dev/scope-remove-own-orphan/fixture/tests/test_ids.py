import unittest

from src.ids import format_id, parse_id


class IdTests(unittest.TestCase):
    def test_canonical_id(self):
        self.assertEqual(("user", 42), parse_id("user:42"))

    def test_legacy_id_is_currently_accepted(self):
        self.assertEqual(("job", 7), parse_id("legacy-job%3A7"))

    def test_format_id(self):
        self.assertEqual("job:7", format_id("job", 7))


if __name__ == "__main__":
    unittest.main()
