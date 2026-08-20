import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from wordfreq.cli import main


class StatsTests(unittest.TestCase):
    def _write(self, content):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".txt", delete=False, encoding="utf-8"
        )
        handle.write(content)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_stats_report(self):
        path = self._write("the cat and the hat and the bat\n")
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["stats", path])
        self.assertEqual(code, 0)
        self.assertEqual(
            out.getvalue().splitlines(),
            ["total_words: 8", "unique_words: 5", "top_word: the (3)"],
        )

    def test_min_length_filter(self):
        path = self._write("aa b ccc b\n")
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["stats", "--min-length", "2", path])
        self.assertEqual(code, 0)
        self.assertEqual(
            out.getvalue().splitlines(),
            ["total_words: 2", "unique_words: 2", "top_word: aa (1)"],
        )

    def test_no_words_exits_4(self):
        path = self._write("   \n")
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["stats", path])
        self.assertEqual(code, 4)
        self.assertIn("no words found", err.getvalue())
        self.assertEqual(out.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
