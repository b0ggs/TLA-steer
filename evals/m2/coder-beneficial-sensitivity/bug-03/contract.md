# Query decoding semantics

Update `solution.py` so that it satisfies all of the following requirements:

- Decode percent escapes, plus-as-space, and UTF-8 text in keys and values.
- Collect repeated keys into lists while preserving their encounter order.
- Retain blank values and raise ValueError for malformed percent escapes.

Regression constraint: Continue decoding a simple single key-value pair.

