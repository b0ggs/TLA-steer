"""Command-line interface wiring for dirlens."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .report import ext_lines, scan_lines


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
    return 0
