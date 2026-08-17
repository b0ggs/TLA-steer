"""Operations that select bookmarks by their labels."""

from collections.abc import Iterable

from .model import Bookmark


def filter_by_label(bookmarks: Iterable[Bookmark], label: str) -> list[Bookmark]:
    """Return bookmarks carrying an exact label, in encounter order."""
    return [bookmark for bookmark in bookmarks if label in bookmark.labels]


# M2-A-006 — Active-list default.  Extend filter_by_label with an
# `include_archived: bool = False` keyword-only parameter.  It continues to
# use exact, case-sensitive label matching and encounter order.  By default it
# excludes archived bookmarks; with include_archived=True it includes both
# active and archived matches.
#
# M2-A-007 — Public API export.  `archive_labeled` must be importable with
# `from bookmarks.labels import archive_labeled` and must be defined in this
# module (not only in the command-line module).
