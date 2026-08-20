"""Command line front end: merge INI files and print the result."""

import sys

from inimerge.errors import ParseError
from inimerge.merger import merge_all
from inimerge.parser import parse
from inimerge.writer import dumps

USAGE = "usage: python -m inimerge.cli FILE [FILE ...]"


def main(argv=None):
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    if not argv:
        print(USAGE, file=sys.stderr)
        return 2
    layers = []
    for path in argv:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                layers.append(parse(handle.read()))
        except OSError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 1
        except ParseError as exc:
            print("error: %s: %s" % (path, exc), file=sys.stderr)
            return 1
    sys.stdout.write(dumps(merge_all(layers)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
