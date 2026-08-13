# Plain-text table rendering

Update `solution.py` so that it satisfies all of the following requirements:

- Implement render_table(rows, columns) with a header, a dash separator row, and one row per mapping, using columns in the supplied order.
- Size each column to its widest stringified value and left-align cells with ' | ' separators.
- Render missing or None values as an empty string and return an empty string when columns is empty.

Regression constraint: Do not mutate the rows or columns supplied by the caller.

