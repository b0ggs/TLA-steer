import unittest

from bookmarks.labels import filter_by_label
from bookmarks.model import Bookmark


class FilterByLabelTests(unittest.TestCase):
    def test_returns_exact_label_matches_in_order(self):
        bookmarks = [
            Bookmark("Python", "https://python.org", ("work",)),
            Bookmark("Weekend", "https://example.test", ("personal",)),
            Bookmark("Docs", "https://docs.python.org", ("work", "reference")),
        ]

        self.assertEqual(
            [bookmark.title for bookmark in filter_by_label(bookmarks, "work")],
            ["Python", "Docs"],
        )


# M2-A-010 — Regression coverage.  Add unit tests in this file using only
# unittest that cover archive_labeled's exact-label behavior, preservation of
# input objects, and a nonmatching bookmark.  Add coverage for filter_by_label
# both with its default and with include_archived=True.
