import unittest
from datetime import date

from datespan.recurrence import expand_recurrence, parse_weekdays


class RecurrenceTests(unittest.TestCase):
    def test_parse_weekdays(self):
        self.assertEqual(parse_weekdays("mon,wed"), [0, 2])

    def test_expand_mondays(self):
        days = expand_recurrence(
            date(2026, 3, 2), date(2026, 3, 13), parse_weekdays("mon")
        )
        self.assertEqual(days, [date(2026, 3, 2), date(2026, 3, 9)])


if __name__ == "__main__":
    unittest.main()
