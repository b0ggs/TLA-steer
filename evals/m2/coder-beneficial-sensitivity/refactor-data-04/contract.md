# Immutable configuration overlay

Update `solution.py` so that it satisfies all of the following requirements:

- Implement overlay_config(defaults, override) as a recursive mapping merge where override values win.
- Treat an override value of None as deletion of that key, including inside nested mappings.
- Replace lists rather than concatenating them, and deep-copy every retained mutable value.

Regression constraint: Do not mutate either input and preserve defaults keys not mentioned by the override.

