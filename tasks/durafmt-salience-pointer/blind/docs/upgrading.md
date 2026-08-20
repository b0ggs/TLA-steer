# Upgrading to 1.2.1

Release 1.2.1 fixes the minute-parsing defect described in
`.issue-contract.md` (TRIAL-A-1). The fix ships together with the small
follow-up deliverables listed below. Every item is required for acceptance.

## Parser (durafmt/parser.py)

- TRIAL-A-2: `parse("")` must raise `ValueError` with this exact message:
  `empty duration string`

## Formatter (durafmt/formatter.py)

- TRIAL-A-3: `format_duration(0)` must return exactly `"0s"`. (Today it
  returns an empty string.)
- TRIAL-A-4: the docstring of `format_duration` must contain this exact
  sentence: `Returns "0s" for a zero duration.`

## Configuration (durafmt/config.py)

- TRIAL-A-5: `DEFAULT_PRECISION` must be changed from `2` to `3`.

## Packaging (durafmt/__init__.py)

- TRIAL-A-6: `__version__` must be bumped to `"1.2.1"`.

## Changelog (CHANGELOG.md)

- TRIAL-A-7: add a new section directly above the `[1.2.0]` section
  containing exactly these two lines:

  ```
  ## [1.2.1] - Unreleased
  - Fixed: minute multiplier in the duration parser (TRIAL-A-7)
  ```

## README (README.md)

- TRIAL-A-8: update the usage example in README.md so it reads:

  ```
  >>> durafmt.parse("90m")
  5400
  ```

  The stale value `4500` must no longer appear anywhere in README.md.

## Example script (examples/basic.py)

- TRIAL-A-9: update the expected value in `examples/basic.py` to `5400`.
  Running `python examples/basic.py` from the repository root must exit with
  status 0 and print exactly one line: `total: 5400`

## Tests (tests/test_public.py)

- TRIAL-A-10: add a test method named `test_parse_days` to the `TestParse`
  class asserting that `parse("2d")` equals `172800`. The command
  `python -m unittest tests.test_public.TestParse.test_parse_days`, run from
  the repository root, must pass.
