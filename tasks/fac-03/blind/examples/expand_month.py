"""Print every Monday in March 2026.

Run from the project root:

    python examples/expand_month.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date

from datespan.recurrence import expand_recurrence, parse_weekdays

for day in expand_recurrence(
    date(2026, 3, 1), date(2026, 3, 31), parse_weekdays("mon")
):
    print(day.isoformat())
