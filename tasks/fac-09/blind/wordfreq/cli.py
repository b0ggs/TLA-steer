"""Command-line interface for wordfreq."""

import argparse
import sys

from . import __version__
from .counter import count_words
from .fileio import read_texts
from .report import render_table, summarize
from .tokenizer import tokenize


def build_parser():
    parser = argparse.ArgumentParser(
        prog="wordfreq",
        description="Build word-frequency reports from plain text files.",
    )
    parser.add_argument(
        "--version", action="version", version="wordfreq %s" % __version__
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_count = subparsers.add_parser(
        "count",
        help="Print the full frequency table.",
        description="Print the full frequency table.",
    )
    p_count.add_argument("files", nargs="+", metavar="FILE")

    p_top = subparsers.add_parser(
        "top",
        help="Print the most frequent words.",
        description="Print the most frequent words.",
    )
    p_top.add_argument("files", nargs="+", metavar="FILE")
    p_top.add_argument("-n", type=int, default=10, help="How many words to show.")

    p_stats = subparsers.add_parser(
        "stats",
        help="Show summary statistics for the input files.",
        description="Show summary statistics for the input files.",
    )
    p_stats.add_argument("files", nargs="+", metavar="FILE")
    p_stats.add_argument(
        "--min-length",
        type=int,
        default=1,
        help="Discard words shorter than N characters.",
        metavar="N",
    )

    return parser


def _gather_words(paths):
    words = []
    for text in read_texts(paths):
        words.extend(tokenize(text))
    return words


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        words = _gather_words(args.files)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    if args.command == "stats":
        words = [word for word in words if len(word) >= args.min_length]

    counts = count_words(words)
    if args.command == "count":
        for line in render_table(counts):
            print(line)
    elif args.command == "top":
        for line in render_table(counts)[: args.n]:
            print(line)
    elif args.command == "stats":
        summary = summarize(counts)
        if summary is None:
            print("no words found", file=sys.stderr)
            return 4
        for line in summary:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
