"""Tests for inimerge.parser."""

import unittest

from inimerge.errors import ParseError
from inimerge.parser import parse


class ParserTests(unittest.TestCase):
    def test_basic_sections(self):
        text = "[db]\nhost = localhost\nport = 5432\n"
        self.assertEqual(
            parse(text), {"db": {"host": "localhost", "port": "5432"}}
        )

    def test_comments_and_blanks_ignored(self):
        text = "# top comment\n[db]\n; note\n\nhost = localhost\n"
        self.assertEqual(parse(text), {"db": {"host": "localhost"}})

    def test_malformed_line_raises(self):
        with self.assertRaises(ParseError):
            parse("[s]\nbogus line\n")


if __name__ == "__main__":
    unittest.main()
