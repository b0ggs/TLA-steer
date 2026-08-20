"""Command line interface: python -m datespan <command> START..END"""

import sys

from .formatting import format_span
from .ranges import expand_range, parse_range


def main(argv):
    if len(argv) != 2 or argv[0] not in ("expand", "span"):
        print("usage: python -m datespan {expand|span} START..END")
        return 2
    start, end = parse_range(argv[1])
    if argv[0] == "expand":
        for day in expand_range(start, end):
            print(day.isoformat())
    else:
        print(format_span(start, end))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
