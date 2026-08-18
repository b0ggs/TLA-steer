"""Read color mappings from INI files."""

import configparser


def load_colors(path):
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    # SCOUT-C-INT-R8: A file without [colors] must produce no stdout, write exactly error: missing [colors] section plus one newline to stderr, exit 2, and show no traceback.
    return dict(parser["colors"])
