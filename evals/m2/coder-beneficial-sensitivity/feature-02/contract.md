# Escaped deep lookup

Update `solution.py` so that it satisfies all of the following requirements:

- Implement deep_get(data, path, default) for dot-separated dictionary keys.
- Treat a backslash-escaped dot as part of a key and a doubled backslash as a literal backslash.
- Allow decimal path components to index lists, returning default for missing keys, invalid indices, or incompatible containers.

Regression constraint: An empty path must return the original root object.

