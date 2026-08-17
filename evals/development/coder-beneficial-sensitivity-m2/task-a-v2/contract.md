# Archive labeled bookmarks

`fixture/` is a small Python package for storing bookmarks in a JSON file.  It
currently supports listing bookmarks by label.  Add an archive operation so a
person can hide a group of bookmarks without deleting their data.

## Required behavior

**M2-A-001 — Primary change.** Add `archive_labeled(bookmarks, label)` to
`bookmarks.labels`.  It accepts a sequence of `Bookmark` values and returns a
new list in the same order.  A bookmark is archived when `label` is one of its
labels; a nonmatching bookmark retains its archived state.

**M2-A-002 — Matching rule.** The `label` argument in `archive_labeled` uses
an exact, case-sensitive string match.  For example, `"work"` matches a label
of `"work"` but not `"Work"` or `"work-notes"`.

**M2-A-003 — Safe update.** `archive_labeled` must not mutate the supplied
sequence or any supplied `Bookmark`.  Its returned list must contain newly
created `Bookmark` objects for every input bookmark, including nonmatches.

**M2-A-004 — Invalid label.** If `label` is not a nonempty string,
`archive_labeled` raises `ValueError`.  It must do so before returning a list.

The public behavior in the files below is part of this request as well.
