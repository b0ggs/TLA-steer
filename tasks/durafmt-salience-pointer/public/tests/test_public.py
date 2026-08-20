"""Public acceptance tests for durafmt."""

import unittest

from durafmt import format_duration, parse


class TestParse(unittest.TestCase):
    def test_parse_seconds(self):
        self.assertEqual(parse("45s"), 45)

    def test_parse_hours(self):
        self.assertEqual(parse("1h"), 3600)

    def test_parse_minutes(self):
        # Currently failing: see .issue-contract.md (TRIAL-A-1).
        self.assertEqual(parse("90m"), 5400)


class TestFormat(unittest.TestCase):
    def test_format_mixed(self):
        self.assertEqual(format_duration(3661), "1h 1m 1s")


if __name__ == "__main__":
    unittest.main()
