import unittest

from pathsieve.loader import load_text


class LoaderTests(unittest.TestCase):
    def test_blank_lines_skipped(self):
        self.assertEqual(len(load_text("\n\n*.log\n")), 1)

    def test_flush_left_comment_skipped(self):
        self.assertEqual(len(load_text("# comment\n*.tmp\n")), 1)


if __name__ == "__main__":
    unittest.main()
