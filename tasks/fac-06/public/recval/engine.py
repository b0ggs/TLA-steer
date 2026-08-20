"""Check a single record against loaded rules."""
from .rules import TYPE_NAMES


def check_record(record, rules):
    """Return a list of (field, problem) tuples; empty when valid."""
    errors = []
    for key in rules["required"]:
        if key not in record:
            errors.append((key, "missing required key"))
    for key, type_name in rules["types"].items():
        if key not in record:
            continue
        value = record[key]
        expected = TYPE_NAMES[type_name]
        if isinstance(value, bool) and type_name != "bool":
            errors.append((key, "expected %s" % type_name))
        elif not isinstance(value, expected):
            errors.append((key, "expected %s" % type_name))
    for key, bounds in rules["ranges"].items():
        if key not in record:
            continue
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        lo, hi = bounds
        if not lo <= value <= hi:
            errors.append((key, "out of range %s..%s" % (lo, hi)))
    return errors
