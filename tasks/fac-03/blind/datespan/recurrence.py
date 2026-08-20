"""Recurring weekday schedules over inclusive date ranges."""

from .ranges import expand_range

WEEKDAY_NAMES = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def parse_weekdays(text):
    """Parse a comma-separated weekday list like 'mon,wed,fri'."""
    names = [part.strip().lower() for part in text.split(",") if part.strip()]
    if not names:
        raise ValueError("recurrence needs at least one weekday")
    numbers = []
    for name in names:
        if name not in WEEKDAY_NAMES:
            raise ValueError("unknown weekday: " + name)
        numbers.append(WEEKDAY_NAMES[name])
    return numbers


def expand_recurrence(start, end, weekdays):
    """Return the dates in the range that fall on the given weekdays."""
    wanted = set(weekdays)
    return [day for day in expand_range(start, end) if day.weekday() in wanted]
