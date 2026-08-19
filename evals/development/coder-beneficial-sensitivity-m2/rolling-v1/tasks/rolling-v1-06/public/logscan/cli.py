"""Command line interface for logscan."""

import argparse
import sys

from . import __version__
from . import parser as _parser


def build_parser():
    ap = argparse.ArgumentParser(
        prog="logscan", description="Tiny log analysis toolkit."
    )
    ap.add_argument(
        "--version", action="version", version="logscan " + __version__
    )
    sub = ap.add_subparsers(dest="command", required=True)

    ap_count = sub.add_parser(
        "count", help="Count parseable records in a log file."
    )
    ap_count.add_argument("path")

    return ap


def _read_records(path):
    with open(path, "r", encoding="utf-8") as fh:
        return _parser.parse_lines(fh)


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "count":
        print(len(_read_records(args.path)))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
