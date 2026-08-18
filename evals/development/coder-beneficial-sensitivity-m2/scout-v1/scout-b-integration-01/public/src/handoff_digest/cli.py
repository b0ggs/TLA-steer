import argparse
import json

from .render import render_record


def build_parser():
    parser = argparse.ArgumentParser(prog="handoff-digest")
    commands = parser.add_subparsers(dest="command", required=True)

    show = commands.add_parser("show")
    show.add_argument("record")
    show.add_argument("--tag", default="TASK")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "show":
        print(render_record(json.loads(args.record), args.tag))
        return 0
    raise AssertionError(f"unsupported command: {args.command}")
