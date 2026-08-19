import unittest

from logscan import parser


class ParseLineTest(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(parser.parse_line("INFO hello"), ("INFO", "hello"))

    def test_message_with_spaces(self):
        self.assertEqual(
            parser.parse_line("ERROR disk on fire"), ("ERROR", "disk on fire")
        )

    def test_malformed_line(self):
        self.assertIsNone(parser.parse_line("nonsense"))

    def test_blank_line(self):
        self.assertIsNone(parser.parse_line("   "))


class ParseLinesTest(unittest.TestCase):
    def test_skips_non_records(self):
        records = parser.parse_lines(["INFO a", "junk", "ERROR b"])
        self.assertEqual(records, [("INFO", "a"), ("ERROR", "b")])


class CountLevelsTest(unittest.TestCase):
    def test_counts(self):
        records = [("INFO", "a"), ("INFO", "b"), ("ERROR", "c")]
        self.assertEqual(parser.count_levels(records), {"INFO": 2, "ERROR": 1})


if __name__ == "__main__":
    unittest.main()
