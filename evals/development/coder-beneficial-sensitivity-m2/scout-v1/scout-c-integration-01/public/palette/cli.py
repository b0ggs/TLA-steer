"""Command-line entry point."""

import argparse
import sys

from .parser import load_colors


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    # SCOUT-C-INT-R3: Add --prefix NAME; for samples/basic.ini with --prefix brand, emit --brand-ink and --brand-paper in the otherwise unchanged CSS block.
    args = parser.parse_args(argv)
    colors = load_colors(args.path)
    sys.stdout.write(repr(colors) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
