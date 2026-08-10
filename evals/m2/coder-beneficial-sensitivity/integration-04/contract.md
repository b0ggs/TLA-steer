# Deep JSON merge command

Update `solution.py` so that it satisfies all of the following requirements:

- Accept two or more JSON object filenames and emit their left-to-right recursive merge as one compact JSON line.
- Recursively merge object values, while later arrays and scalar values replace earlier values entirely.
- For too few files, invalid JSON, or a non-object root, exit 2 with an error on stderr and no traceback.

Regression constraint: Sort output object keys for deterministic output regardless of input key order.

