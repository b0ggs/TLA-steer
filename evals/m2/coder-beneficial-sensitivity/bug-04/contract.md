# Atomic inventory operations

Update `solution.py` so that it satisfies all of the following requirements:

- Apply add and remove operations sequentially and return the resulting stock mapping.
- If any removal exceeds available stock, raise ValueError and leave the caller's mapping unchanged.
- Reject unknown operation names and negative quantities with ValueError.

Regression constraint: A successful call must also leave the caller's input mapping unchanged.

