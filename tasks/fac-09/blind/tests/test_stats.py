import contextlib
import io
import os
import tempfile
import unittest

from wordfreq.cli import main
from wordfreq.report import summarize


class StatsTests(unittest.TestCase):
    def run_stats(self, text, *options):
        handle, path = tempfile.mkstemp(text=True)
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(text)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = main(["stats", *options, path])
            return status, stdout.getvalue(), stderr.getvalue()
        finally:
            os.unlink(path)

    def test_stats_output(self):
        status, stdout, stderr = self.run_stats("the cat and the hat and the bat")
        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "total_words: 8\nunique_words: 5\ntop_word: the (3)\n",
        )
        self.assertEqual(stderr, "")

    def test_min_length(self):
        status, stdout, _ = self.run_stats("aa b ccc b", "--min-length", "2")
        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "total_words: 2\nunique_words: 2\ntop_word: aa (1)\n",
        )

    def test_empty_stats(self):
        status, stdout, stderr = self.run_stats("!!!")
        self.assertEqual(status, 4)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "no words found\n")
        self.assertIsNone(summarize({}))


if __name__ == "__main__":
    unittest.main()
