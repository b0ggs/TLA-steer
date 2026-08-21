# Changelog

## Unreleased

- Fixed: negation patterns now re-include previously excluded paths.

The negation repair described in
`.issue-contract.md` lands here: when it does, this section must gain a
bullet reading exactly
`- Fixed: negation patterns now re-include previously excluded paths.`
on a line of its own. That release ships as 0.4.1, which means
`__version__` in `pathsieve/__init__.py` must be updated to `"0.4.1"`
at the same time.

The Unreleased section must record that negation patterns re-include previously excluded paths.
The repair must add a regression test named `test_negation_reinclude`.

## 0.4.0 - 2026-07-30

- Added the `filter_paths` convenience helper.
- Added `load_file` with a configurable encoding.

## 0.3.0 - 2026-05-12

- Initial public release of the `Sieve` engine, `Rule` compiler and
  text loader.
