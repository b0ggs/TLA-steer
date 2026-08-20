"""Command-line interface for colstat."""

import sys

from . import __version__, config, formats, reader, stats


def main(argv=None):
    """Run the colstat command line and return an exit status."""
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] in ("--version", "-V"):
        print("colstat %s" % __version__)
        return 0
    if len(argv) < 3 or argv[0] != "stats":
        print("usage: colstat stats FILE COLUMN [PRECISION]", file=sys.stderr)
        return 1
    path, name = argv[1], argv[2]
    precision = int(argv[3]) if len(argv) > 3 else config.DEFAULT_PRECISION
    header, data_rows = reader.load_rows(path, delimiter=config.DEFAULT_DELIMITER)
    try:
        values = reader.column(header, data_rows, name)
    except LookupError:
        print("colstat: unknown column: %s" % name, file=sys.stderr)
        return 2
    summary = stats.column_summary(values, precision)
    print(formats.render_json(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
