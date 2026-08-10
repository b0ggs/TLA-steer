# Stable record deduplication

Update `solution.py` so that it satisfies all of the following requirements:

- Implement dedupe_records(records, key='id') so one record remains per key value, in first-occurrence order.
- For duplicates, keep the complete contents of the last record rather than merging fields.
- Raise ValueError identifying the zero-based row index when a record lacks the requested key.

Regression constraint: Return independent dictionaries and do not mutate the input sequence or its records.

