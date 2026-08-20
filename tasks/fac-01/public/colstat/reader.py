"""CSV loading helpers for colstat."""

import csv


def load_rows(path, delimiter=","):
    """Read a CSV file and return a (header, data_rows) pair."""
    with open(path, newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))
    header = rows[0]
    return header, rows[1:]


def column(header, data_rows, name):
    """Extract one named column as a list of floats."""
    if name not in header:
        raise LookupError(name)
    index = header.index(name)
    return [float(row[index]) for row in data_rows]
