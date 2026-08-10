# Recursive field masking

Update `solution.py` so that it satisfies all of the following requirements:

- Implement mask_fields(value, names, replacement='***') to replace matching dictionary values recursively.
- Match field names case-insensitively and recurse through dictionaries nested inside lists and tuples.
- Return a deep independent result without changing the input, preserving tuple versus list container types.

Regression constraint: Values under nonmatching keys must remain equal to their originals.

