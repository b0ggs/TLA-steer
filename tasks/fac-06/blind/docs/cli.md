# recval command reference

`recval` is invoked as `python -m recval SUBCOMMAND ...`.

Global options:

- `--version` — print `recval <version>` and exit 0.

## validate

    python -m recval validate RULES RECORDS

Checks every record in RECORDS (a JSON Lines file, one JSON object per
line) against RULES (a schema-lite JSON rules file). Prints one line per
validation error, in file order, using the format:

    record LINENO: FIELD: PROBLEM

where PROBLEM is one of `missing required key`, `expected TYPENAME`, or
`out of range LO..HI`.

Exit codes:

- `0` — every record is valid; prints `ok`.
- `1` — at least one validation error was printed.
- `2` — the records file does not exist; prints
  `error: records file not found: PATH` to stderr.

Example, using the files in `examples/`:

    $ python -m recval validate examples/rules.json examples/records.jsonl
    record 3: name: missing required key
    record 5: age: out of range 0..130

## rules

    python -m recval rules RULES

Prints a readable one-line-per-section summary of a rules file
(`required:`, `types:`, `ranges:`) with keys sorted alphabetically, then
exits 0.

## summarize (to be implemented)

Acceptance notes:

- FAC06-1: Add a `summarize` subcommand invoked as
  `python -m recval summarize RULES RECORDS`. It checks every record
  against the rules and prints one JSON object to stdout with exactly
  these four top-level keys: `total`, `valid`, `invalid`,
  `errors_by_field`. Whenever it prints a summary it exits 0, even if
  some records are invalid.
- FAC06-2: `errors_by_field` maps each field name to the number of
  validation errors recorded for that field, with keys sorted
  alphabetically, and the JSON object is printed with 2-space
  indentation. Running
  `python -m recval summarize examples/rules.json examples/records.jsonl`
  must print exactly:

      {
        "total": 6,
        "valid": 4,
        "invalid": 2,
        "errors_by_field": {
          "age": 1,
          "name": 1
        }
      }

- FAC06-3: `python -m recval summarize --help` must exit 0 and its
  output must contain this sentence verbatim:
  `Summarize validation results as machine-readable JSON counts.`
- FAC06-4: When the records file does not exist, `summarize` prints
  `error: records file not found: PATH` (with the given path) to stderr
  and exits 2, matching `validate`.
- FAC06-8: Add to the Defaults list in README.md this exact line:
  `Default summary indent: 2 spaces.`
