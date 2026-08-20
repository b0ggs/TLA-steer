# datespan behavior notes

This document records the exact behavior that the 0.4.1 maintenance release
must ship. Acceptance notes are tagged FAC03-*.

## Ranges (`datespan/ranges.py`)

- FAC03-4: The `expand_range` docstring must contain this exact sentence:
  `The end date is included in the result.`
- FAC03-8: When the range text does not contain the `..` separator,
  `parse_range` must raise `ValueError` with this exact message:
  `invalid range: expected START..END`

## Recurrence (`datespan/recurrence.py`)

- FAC03-6: When the weekday list is empty or contains only whitespace and
  commas (for example `parse_weekdays("")`), `parse_weekdays` must raise
  `ValueError` with this exact message:
  `recurrence needs at least one weekday`

## Leap years (`datespan/utils.py`)

- FAC03-10: `is_leap_year` must implement the full Gregorian rule:
  `is_leap_year(2000)` is `True`, `is_leap_year(1900)` is `False`, and
  `is_leap_year(2024)` is `True`.

## Changelog (`CHANGELOG.md`)

- FAC03-2: `CHANGELOG.md` must gain a new section whose heading line is
  exactly `## 0.4.1`, and that section must contain this exact bullet line:
  `- Fixed: expand_range now includes the end date.`
