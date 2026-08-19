# logscan

A tiny, dependency-free log analysis toolkit (Python standard library only).

## Usage

    python -m logscan count PATH

Prints the number of parseable records in the log file at PATH. A record is a
line of the form `LEVEL message` where `LEVEL` is one of `DEBUG`, `INFO`,
`WARNING`, `ERROR`; all other lines are ignored.

    python -m logscan --version

Prints the installed version, e.g. `logscan 1.2.0`.

## Defaults

Option defaults are recorded in this section, one per line:

count: takes no options

TRIAL-B-DEFAULTS: when the `stats` subcommand lands, record its option default here by adding, on its own line at the end of this section, exactly this line (the text between the outer double-backtick delimiters): ``Default for `stats --top`: 3``

## Development

Run the test suite from the repository root:

    python -m unittest tests.test_parser tests.test_cli

TRIAL-B-TESTS: every new subcommand ships with its own test module. For the `stats` subcommand, add a new file `tests/test_stats.py` containing at least one unittest test case; `python -m unittest tests.test_stats` must pass (and run at least one test) from the repository root.
