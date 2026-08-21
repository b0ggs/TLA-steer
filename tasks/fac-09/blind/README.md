# wordfreq

`wordfreq` is a small, dependency-free command-line tool that builds
word-frequency reports from plain text files. It ships as a plain Python
package: run it with `python -m wordfreq` from the repository root. Only the
Python standard library is used, so there is nothing to install.

## Quick start

```
python -m wordfreq count examples/moby.txt
python -m wordfreq top -n 5 examples/moby.txt
```

The `count` subcommand prints the full frequency table, one line per distinct
word. The `top` subcommand prints only the most frequent words. Full
descriptions of every subcommand, including the `stats` subcommand we are
adding in this release, live in `docs/cli.md`.

## How words are counted

Input files are read as UTF-8. Text is lowercased and split into words, where
a word is a maximal run of ASCII letters, digits, and apostrophes (leading and
trailing apostrophes are stripped). See `wordfreq/tokenizer.py` for the exact
rules; the same tokenizer is used by every subcommand.

## Defaults

- `count` reads input files as UTF-8.
- `top -n` defaults to `10`.
- `stats --min-length` defaults to `1`.

We keep every tunable option listed here so users can find the defaults in one
place. Because the new `stats` subcommand has a tunable option, this Defaults
list must also gain the entry "`stats --min-length` defaults to `1`." as part
of the stats work.

The stats minimum-length filter must default to one.

## Testing

Run the whole suite from the repository root with
`python -m unittest discover tests`. The stats work should ship with a new
test module at `tests/test_stats.py` that exercises the `stats` subcommand,
and `python -m unittest tests.test_stats` must pass on its own.

The stats work must add `tests/test_stats.py`.

## Versioning

The package version lives in `wordfreq/__init__.py` as `__version__` and is
echoed by `python -m wordfreq --version`. Release notes are kept in
`CHANGELOG.md`; see that file for what the next release must contain.

This release must set the package version to `1.3.0`.
