"""Command line interface for logrotor."""

import argparse
import os
import sys

from logrotor import __version__, rotate, scan


def build_parser():
    parser = argparse.ArgumentParser(
        prog="logrotor",
        description="Rotate and archive log files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="logrotor " + __version__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_rotate = subparsers.add_parser(
        "rotate",
        help="Rotate every *.log file in a directory.",
        description="Rotate every *.log file in a directory.",
    )
    parser_rotate.add_argument("directory", help="Directory containing log files.")

    parser_list = subparsers.add_parser(
        "list",
        help="List rotated archives in a directory.",
        description="List rotated archives in a directory.",
    )
    parser_list.add_argument("directory", help="Directory containing archives.")

    return parser


def cmd_rotate(args):
    for name, archive in rotate.rotate_directory(args.directory):
        print("rotated: %s -> %s" % (name, archive))
    return 0


def cmd_list(args):
    names = []
    for name in os.listdir(args.directory):
        if scan.ARCHIVE_PATTERN.match(name):
            names.append(name)
    for name in sorted(names):
        print(name)
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not os.path.isdir(args.directory):
        print("error: no such directory: " + args.directory, file=sys.stderr)
        return 3
    if args.command == "rotate":
        return cmd_rotate(args)
    if args.command == "list":
        return cmd_list(args)
    parser.error("unknown command: %s" % args.command)
