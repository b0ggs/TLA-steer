"""Calendar helper utilities."""

MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def is_leap_year(year):
    """Return True when the year is a Gregorian leap year."""
    return year % 4 == 0 and year % 100 != 0


def days_in_month(year, month):
    """Return the number of days in the given month."""
    if month == 2 and is_leap_year(year):
        return 29
    return MONTH_LENGTHS[month - 1]
