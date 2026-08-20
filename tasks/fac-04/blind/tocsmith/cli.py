"""Command-line interface for tocsmith."""

import argparse
import json
import sys

from . import __version__
from .render import render_markdown
from .scanner import scan_text
from .toc import build_entries

PROG = "tocsmith"


def _read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        reason = exc.strerror or str(exc)
        print(
            "{}: error: cannot read {}: {}".format(PROG, path, reason),
            file=sys.stderr,
        )
        raise SystemExit(2)


def build_parser():
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Generate tables of contents for Markdown files.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="{} {}".format(PROG, __version__),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser(
        "generate",
        help="Print a Markdown table of contents for FILE.",
        description="Print a Markdown table of contents for FILE.",
    )
    generate.add_argument("file", help="Markdown file to scan.")

    json_command = subparsers.add_parser(
        "json",
        help="Emit the table of contents as JSON instead of Markdown.",
        description="Emit the table of contents as JSON instead of Markdown.",
    )
    json_command.add_argument("file", help="Markdown file to scan.")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        text = _read_file(args.file)
        entries = build_entries(scan_text(text))
        sys.stdout.write(render_markdown(entries))
        return 0

    if args.command == "json":
        text = _read_file(args.file)
        entries = build_entries(scan_text(text))
        sys.stdout.write(json.dumps(entries, indent=2) + "\n")
        return 0 if entries else 3

    return 0
