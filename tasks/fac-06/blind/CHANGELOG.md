# Changelog

## 0.3.0

- Added the summarize subcommand.

## Unreleased

- FAC06-9: For the summarize release, set `__version__` in
  `recval/__init__.py` to `0.3.0`; `python -m recval --version` must
  then print exactly `recval 0.3.0`.

## 0.2.0

- Added the `rules` subcommand.
- `validate` now exits 2 and prints `error: records file not found: PATH`
  to stderr when the records file does not exist.

## 0.1.0

- Initial release with the `validate` subcommand.
