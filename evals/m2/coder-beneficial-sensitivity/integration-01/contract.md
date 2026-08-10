# JSON summing command

Update `solution.py` so that it satisfies all of the following requirements:

- When run, read a JSON array from standard input and write exactly one JSON object containing its numeric total.
- Support --field NAME to sum that field from each object, treating a missing or null field as zero.
- For malformed JSON, a non-array root, or a nonnumeric selected value, exit with status 2 and a concise stderr message without a traceback.

Regression constraint: Accept surrounding whitespace and preserve integer totals as JSON integers.

