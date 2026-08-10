# UTC event grouping

Update `solution.py` so that it satisfies all of the following requirements:

- Implement group_events(events) grouping records by the UTC calendar date of their ISO-8601 timestamp field.
- Accept Z and explicit numeric offsets, and return date keys in ascending order.
- Within each group, order records by instant and preserve input order when instants are equal.

Regression constraint: Return copied record dictionaries and leave the input and its ordering unchanged.

