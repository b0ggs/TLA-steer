# Cycle-safe tree flattening

Update `solution.py` so that it satisfies all of the following requirements:

- Implement flatten_tree(value) yielding (path_tuple, leaf_value) pairs for leaves in nested dictionaries and lists.
- Traverse dictionary insertion order and list index order, with an empty dictionary or list treated as a leaf.
- Detect a container cycle on the current ancestry and raise ValueError instead of recursing forever.

Regression constraint: Shared but acyclic subcontainers may appear at multiple paths, and input containers must not be modified.

