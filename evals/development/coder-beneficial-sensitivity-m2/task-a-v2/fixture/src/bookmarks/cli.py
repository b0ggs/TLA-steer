"""Command-line entry point for bookmark files."""

import argparse
import json
from pathlib import Path

from .labels import filter_by_label
from .model import bookmark_from_dict


def read_bookmarks(path: Path):
    with path.open(encoding="utf-8") as handle:
        return [bookmark_from_dict(value) for value in json.load(handle)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--label", required=True)
    arguments = parser.parse_args(argv)
    for bookmark in filter_by_label(read_bookmarks(arguments.input), arguments.label):
        print(bookmark.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# M2-A-008 — Command-line entry.  Add an `archive` subcommand to
# `python -m bookmarks.cli`.  It requires `--input PATH`, `--output PATH`, and
# `--label LABEL`.  It reads the input JSON array using bookmark_from_dict,
# archives it with archive_labeled, and writes a JSON array of each result's
# to_dict() value to the output path in the same order.  The archive command
# must not write to the input path.  On success it writes no stdout or stderr
# and returns exit status 0.  The existing listing invocation may remain
# available with its current arguments.
