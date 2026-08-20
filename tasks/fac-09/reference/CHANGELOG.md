# Changelog

All notable changes to wordfreq are recorded here, newest first.

## Unreleased

The stats work described in `docs/cli.md` will ship as release 1.3.0. When it
lands, start a `## 1.3.0` section in this file containing the line
`Added the stats subcommand.` Releasing 1.3.0 also means bumping
`__version__` in `wordfreq/__init__.py` to `1.3.0`, after which
`python -m wordfreq --version` prints `wordfreq 1.3.0`.

## 1.3.0

- Added the stats subcommand.
- Bumped `__version__` to `1.3.0`.

## 1.2.0

- Added the `top` subcommand with the `-n` option.
- Documented the tokenizer rules in `README.md`.

## 1.1.0

- Added `merge_counts` so multiple files aggregate into one table.
- `count` now accepts more than one FILE argument.

## 1.0.0

- Initial release: `count` subcommand, tokenizer, and frequency table.
