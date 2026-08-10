# Unique-lines command

Update `solution.py` so that it satisfies all of the following requirements:

- Read lines from stdin by default and emit the first occurrence of each distinct line in encounter order.
- With -i or --ignore-case, compare using Unicode case folding while preserving the spelling of the first occurrence.
- Accept an optional input filename and support --count, which prefixes each emitted line with its occurrence count and a tab.

Regression constraint: Output must end with one newline when at least one line is emitted and be empty for empty input.

