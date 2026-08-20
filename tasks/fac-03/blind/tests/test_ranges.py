import unittest
from datetime import date

from datespan.ranges import expand_range, parse_range

# FAC03-7: For release 0.4.1, add a test method named exactly
# test_range_includes_end_date to RangeTests below. It must assert that
# expand_range(date(2026, 3, 1), date(2026, 3, 3)) returns three dates
# ending with date(2026, 3, 3). After the change,
# `python -m unittest tests.test_ranges` run from the project root must
# pass.


class RangeTests(unittest.TestCase):
    def test_parse_range_valid(self):
        self.assertEqual(
            parse_range("2026-03-01..2026-03-05"),
            (date(2026, 3, 1), date(2026, 3, 5)),
        )

    def test_parse_range_end_before_start(self):
        with self.assertRaises(ValueError):
            parse_range("2026-03-05..2026-03-01")

    def test_expand_range_starts_at_start(self):
        days = expand_range(date(2026, 3, 1), date(2026, 3, 3))
        self.assertEqual(days[0], date(2026, 3, 1))

    def test_range_includes_end_date(self):
        days = expand_range(date(2026, 3, 1), date(2026, 3, 3))
        self.assertEqual(
            days,
            [date(2026, 3, 1), date(2026, 3, 2), date(2026, 3, 3)],
        )


if __name__ == "__main__":
    unittest.main()
