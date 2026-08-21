# Changelog

## Unreleased

- Fixed: negation patterns now re-include previously excluded paths.
- Fixed: indented comment lines are recognised by the loader.
- Fixed: `filter_paths` preserves input order instead of sorting.
- Fixed: `compile_pattern("!")` now raises `PatternError`.
- Changed: `ignore_case` on `Sieve` defaults to `False` as documented.
- Added: `PatternError` is re-exported from the package root.
- Bumped `__version__` to `"0.4.1"`.

The Unreleased section must record that negation patterns re-include previously excluded paths.
The repair must add a regression test named `test_negation_reinclude`.

## 0.4.0 - 2026-07-30

- Added the `filter_paths` convenience helper.
- Added `load_file` with a configurable encoding.

## 0.3.0 - 2026-05-12

- Initial public release of the `Sieve` engine, `Rule` compiler and
  text loader.
