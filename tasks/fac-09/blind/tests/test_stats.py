import contextlib
import io
import os
import tempfile
import unittest

from wordfreq.cli import build_parser, main
from wordfreq.report import summarize


class StatsTests(unittest.TestCase):
    def run_stats(self, text, *options):
        handle = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False
        )
        try:
            with handle:
                handle.write(text)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(
                stderr
            ):
                status = main(["stats", *options, handle.name])
            return status, stdout.getvalue(), stderr.getvalue()
        finally:
            os.unlink(handle.name)

    def test_prints_three_line_summary_with_alphabetical_tiebreak(self):
        status, stdout, stderr = self.run_stats("the cat and the hat and the bat")

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "total_words: 8\nunique_words: 5\ntop_word: the (3)\n",
        )
        self.assertEqual(stderr, "")

    def test_min_length_filters_before_counting(self):
        status, stdout, stderr = self.run_stats("aa b ccc b", "--min-length", "2")

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "total_words: 2\nunique_words: 2\ntop_word: aa (1)\n",
        )
        self.assertEqual(stderr, "")

    def test_min_length_defaults_to_one(self):
        args = build_parser().parse_args(["stats", "input.txt"])

        self.assertEqual(args.min_length, 1)

    def test_empty_result_writes_error_and_returns_four(self):
        status, stdout, stderr = self.run_stats("a bb", "--min-length", "3")

        self.assertEqual(status, 4)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "no words found\n")

    def test_summarize_returns_none_for_empty_mapping(self):
        self.assertIsNone(summarize({}))


if __name__ == "__main__":
    unittest.main()
