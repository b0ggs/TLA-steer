"""Command-line interface wiring for dirlens."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .report import ext_lines, newest_entries, scan_lines


def non_negative_int(value):
    """Return *value* as an integer, rejecting negative limits."""
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return number


def build_parser():
    parser = argparse.ArgumentParser(
        prog="dirlens",
        description="Inventory the files in a directory tree.",
    )
    parser.add_argument(
        "--version", action="version", version="dirlens %s" % __version__
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser(
        "scan", help="List every file with its size in bytes."
    )
    p_scan.add_argument("path")

    p_ext = sub.add_parser("ext", help="Summarise file counts by extension.")
    p_ext.add_argument("path")

    newest_help = "List the most recently modified files in a directory tree."
    p_newest = sub.add_parser(
        "newest", help=newest_help, description=newest_help
    )
    p_newest.add_argument("path")
    p_newest.add_argument("--limit", type=non_negative_int, default=5)
    p_newest.add_argument("--json", action="store_true")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.path)
    if not root.exists():
        print("dirlens: path does not exist: %s" % root, file=sys.stderr)
        return 3

    if args.command == "scan":
        for line in scan_lines(root):
            print(line)
    elif args.command == "ext":
        for line in ext_lines(root):
            print(line)
    elif args.command == "newest":
        entries = newest_entries(root, args.limit)
        if args.json:
            print(json.dumps(entries))
        else:
            for entry in entries:
                print("%s\t%s" % (entry["mtime"], entry["path"]))
    return 0
