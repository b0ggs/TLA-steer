# Lazy iterable chunking

Update `solution.py` so that it satisfies all of the following requirements:

- Implement chunked(iterable, size) yielding tuples of at most size items, including a short final tuple.
- Support an optional fill keyword that pads only the final tuple; omitting fill must not pad.
- Raise ValueError for nonpositive sizes and avoid consuming the source until iteration begins.

Regression constraint: Do not mutate a list used as the source iterable.

