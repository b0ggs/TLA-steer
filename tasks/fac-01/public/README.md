# colstat

A small, standard-library-only tool that computes summary statistics for a
numeric column of a CSV file.

## Usage

    python -m colstat.cli stats examples/scores.csv score

Prints a JSON summary of the `score` column. An optional trailing argument
overrides the rounding precision:

    python -m colstat.cli stats examples/scores.csv score 2

## Version

FAC01-2: For the 0.4.1 release, `colstat/__init__.py` must set
`__version__ = "0.4.1"`.

FAC01-9: `python -m colstat.cli --version` must print exactly this line to
stdout and exit with status 0:

    colstat 0.4.1

## Errors

FAC01-8: When the requested column does not exist, the CLI must write a
single line to stderr and exit with status 2. The general form is
`colstat: unknown column: <name>`. For example,
`python -m colstat.cli stats examples/scores.csv nosuchcol` must write
exactly this line to stderr:

    colstat: unknown column: nosuchcol

## Testing

Run the suite with:

    python -m unittest discover -s tests -t .

See the FAC01-7 note in `tests/test_stats.py` for a required new test.

## Documentation

Statistical definitions and output-format rules live in
`docs/algorithms.md`. Release history and release-process notes live in
`CHANGELOG.md`.
