"""Build machine-readable validation summaries."""
from .engine import check_record


def summarize_records(records, rules):
    """Return the summary dict for (lineno, record) pairs under rules."""
    total = valid = invalid = 0
    by_field = {}
    for _lineno, record in records:
        total += 1
        errors = check_record(record, rules)
        if errors:
            invalid += 1
            for field, _problem in errors:
                by_field[field] = by_field.get(field, 0) + 1
        else:
            valid += 1
    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "errors_by_field": {key: by_field[key] for key in sorted(by_field)},
    }
