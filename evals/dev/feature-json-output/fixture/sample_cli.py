"""A tiny greeting command."""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args(argv)
    print(f"Hello, {args.name}!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
