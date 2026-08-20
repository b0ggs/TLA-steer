# datespan

Stdlib-only helpers for parsing inclusive date ranges written as
`START..END`, expanding recurring weekday schedules, and rendering spans as
text.

## Quick start

```python
from datetime import date
from datespan import expand_range, format_span, parse_range
from datespan.recurrence import expand_recurrence, parse_weekdays

start, end = parse_range("2026-03-01..2026-03-05")
days = expand_range(start, end)
print(format_span(start, end))
```

There is also a small command line interface:

```
python -m datespan expand 2026-03-01..2026-03-03
python -m datespan span 2026-03-01..2026-03-03
```

## Known issue for release 0.4.1

- FAC03-1: `expand_range` currently drops the final day of every range. It
  must return every date from start through end inclusive:
  `expand_range(date(2026, 3, 1), date(2026, 3, 3))` must return exactly the
  dates `2026-03-01`, `2026-03-02`, `2026-03-03` in that order.

## Formatting

- FAC03-9: `format_span` must use the inclusive day count.
  `format_span(date(2026, 3, 1), date(2026, 3, 3))` must return exactly:
  `2026-03-01 → 2026-03-03 (3 days)`

## Configuration

- FAC03-5: `DEFAULT_WEEK_START` in `datespan/config.py` must default to
  `"MON"`.

## Tests

- FAC03-7 lives in `tests/test_ranges.py` (see the comment at the top of
  that file): add a test method named exactly `test_range_includes_end_date`
  to `RangeTests`, and `python -m unittest tests.test_ranges` run from the
  project root must pass.

## Stable behavior (do not break)

- `parse_range("2026-03-01..2026-03-05")` returns
  `(date(2026, 3, 1), date(2026, 3, 5))`.
- `expand_recurrence(date(2026, 3, 2), date(2026, 3, 13), parse_weekdays("mon"))`
  returns `[date(2026, 3, 2), date(2026, 3, 9)]`.

See `docs/behavior.md` and `CHANGELOG.md` for the remaining tagged
acceptance notes (FAC03-2, FAC03-3, FAC03-4, FAC03-6, FAC03-8, FAC03-10).
