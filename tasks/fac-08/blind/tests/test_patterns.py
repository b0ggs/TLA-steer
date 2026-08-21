import unittest

from pathsieve.errors import PatternError
from pathsieve.patterns import compile_pattern


class CompileTests(unittest.TestCase):
    def test_blank_pattern_rejected(self):
        with self.assertRaises(PatternError):
            compile_pattern("   ")

    def test_lone_negation_rejected(self):
        with self.assertRaisesRegex(
            PatternError, "^negation requires a pattern body$"
        ):
            compile_pattern("!")

    def test_star_does_not_cross_directories(self):
        rule = compile_pattern("docs/*.md")
        self.assertTrue(rule.matches("docs/guide.md"))
        self.assertFalse(rule.matches("docs/deep/guide.md"))

    def test_segment_match_without_slash(self):
        rule = compile_pattern("*.log")
        self.assertTrue(rule.matches("srv/app.log"))
        self.assertFalse(rule.matches("srv/app.txt"))


if __name__ == "__main__":
    unittest.main()
