"""Parsing and expansion of inclusive date ranges."""

from datetime import date, timedelta


def parse_range(text):
    """Parse 'START..END' (two ISO dates) into a (start, end) tuple."""
    if ".." not in text:
        raise ValueError("bad range")
    start_text, _, end_text = text.partition("..")
    start = date.fromisoformat(start_text.strip())
    end = date.fromisoformat(end_text.strip())
    if end < start:
        raise ValueError("range end before start")
    return start, end


def expand_range(start, end):
    """Return a list of the dates covered by the range."""
    days = []
    current = start
    while current < end:
        days.append(current)
        current += timedelta(days=1)
    return days
