"""Command-line interface for recval."""
import argparse
import sys

from . import __version__
from .engine import check_record
from .loader import iter_records
from .rules import load_rules


def build_parser():
    parser = argparse.ArgumentParser(
        prog="recval",
        description="Validate JSON Lines records against schema-lite rules.",
    )
    parser.add_argument(
        "--version", action="version", version="recval %s" % __version__
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate",
        help="Validate records and print one line per validation error.",
        description="Validate records and print one line per validation error.",
    )
    p_validate.add_argument("rules", help="Path to a rules JSON file.")
    p_validate.add_argument("records", help="Path to a JSON Lines records file.")

    p_rules = sub.add_parser(
        "rules",
        help="Print a readable summary of a rules file.",
        description="Print a readable summary of a rules file.",
    )
    p_rules.add_argument("rules", help="Path to a rules JSON file.")
    return parser


def cmd_validate(args):
    rules = load_rules(args.rules)
    try:
        records = iter_records(args.records)
    except FileNotFoundError:
        print("error: records file not found: %s" % args.records, file=sys.stderr)
        return 2
    found_errors = False
    for lineno, record in records:
        for field, problem in check_record(record, rules):
            found_errors = True
            print("record %d: %s: %s" % (lineno, field, problem))
    if found_errors:
        return 1
    print("ok")
    return 0


def cmd_rules(args):
    rules = load_rules(args.rules)
    print("required: %s" % ", ".join(rules["required"]))
    print("types: %s" % ", ".join(
        "%s=%s" % (key, rules["types"][key]) for key in sorted(rules["types"])
    ))
    print("ranges: %s" % ", ".join(
        "%s=%s..%s" % (key, rules["ranges"][key][0], rules["ranges"][key][1])
        for key in sorted(rules["ranges"])
    ))
    return 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "rules":
        return cmd_rules(args)
    parser.error("unknown command %r" % args.command)


if __name__ == "__main__":
    sys.exit(main())
