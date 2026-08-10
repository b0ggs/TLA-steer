# Range merge correctness

Update `solution.py` so that it satisfies all of the following requirements:

- Normalize each endpoint pair so reversed ranges are accepted.
- Merge both overlapping ranges and ranges that touch at an endpoint.
- Return ranges in ascending order without mutating the input list or its nested pairs.

Regression constraint: Continue returning disjoint already-sorted ranges unchanged in value.

