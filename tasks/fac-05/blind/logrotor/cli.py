"""Command line interface for logrotor."""

import argparse
import os
import sys

from logrotor import __version__, prune, rotate, scan


def _nonnegative_int(text):
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return value


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

    parser_prune = subparsers.add_parser(
        "prune",
        help="Remove old rotated archives, keeping the newest N per log.",
        description="Remove old rotated archives, keeping the newest N per log.",
    )
    parser_prune.add_argument(
        "--keep",
        type=_nonnegative_int,
        default=5,
        metavar="N",
        help="Number of newest archives to retain per log (default: 5).",
    )
    parser_prune.add_argument(
        "--dry-run",
        action="store_true",
        help="Report archives without deleting them.",
    )
    parser_prune.add_argument("directory", help="Directory containing archives.")

    return parser


def cmd_rotate(args):
    for name, archive in rotate.rotate_directory(args.directory):
        print("rotated: %s -> %s" % (name, archive))
    return 0


def cmd_list(args):
    for name in scan.find_archives(args.directory):
        print(name)
    return 0


def cmd_prune(args):
    names = prune.prune_directory(args.directory, args.keep, args.dry_run)
    if not names:
        print("nothing to prune")
        return 0
    prefix = "would prune: " if args.dry_run else "pruned: "
    for name in names:
        print(prefix + name)
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
    if args.command == "prune":
        return cmd_prune(args)
    parser.error("unknown command: %s" % args.command)
