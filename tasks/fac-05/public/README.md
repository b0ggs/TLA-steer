# logrotor

A small, stdlib-only utility for rotating and archiving application log
files. It is run as a module:

```
python -m logrotor rotate logs/
python -m logrotor list logs/
```

`rotate` renames each `NAME.log` file in the directory to a timestamped
archive (`NAME.log.YYYYMMDDHHMMSS`) and recreates an empty `NAME.log`.
`list` prints the archives that have accumulated. The full command
reference lives in `docs/cli.md`, and recorded sessions live in
`examples/`.

## Defaults

- `rotate` processes every `*.log` file in the named directory.
- Archive timestamps are taken from the UTC clock.
- `list` prints archive filenames in ascending order, one per line.

## Running the tests

The test suite uses only `unittest`:

```
python -m unittest tests.test_rotate tests.test_scan
```

## Acceptance notes

> **FAC05-6 (acceptance note).** The new `prune` subcommand's `--keep`
> option defaults to `5`: running `prune` without `--keep` keeps the 5
> newest archives per log and deletes the rest. Document this by adding
> the following bullet line, verbatim, to the `## Defaults` section
> above:
>
> `- The default retention for prune is 5 archives per log.`

> **FAC05-9 (acceptance note).** Ship at least one test for the new
> subcommand in a new file `tests/test_prune.py`. The command
> `python -m unittest tests.test_prune` must exit with status 0 and run
> at least one test, from any working directory, when the repository
> root is on `PYTHONPATH`.
