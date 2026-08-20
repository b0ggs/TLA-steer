# recval

Stdlib-only CLI that validates JSON Lines records against a schema-lite
rules file: required keys, per-key types, and numeric ranges.

## Usage

    python -m recval validate examples/rules.json examples/records.jsonl
    python -m recval rules examples/rules.json

The full command reference lives in [docs/cli.md](docs/cli.md); sample
inputs live in [examples/](examples/).

## Rules format

A rules file is a JSON object with up to three sections:

    {
      "required": ["id", "name", "age"],
      "types": {"id": "int", "name": "str", "age": "int", "email": "str"},
      "ranges": {"age": [0, 130]}
    }

Type names: `int`, `float`, `str`, `bool`, `list`, `dict`.

## Defaults

- Default records encoding: UTF-8.
- Omitted rules sections default to `required=[]`, `types={}`,
  `ranges={}`.
- Default summary indent: 2 spaces.

## Testing

    python -m unittest discover -s tests -v

## Acceptance notes

- FAC06-5: An empty (zero-byte) records file must be treated as zero
  records: change `recval/loader.py` so that `iter_records` returns an
  empty list for an empty file instead of raising `LoaderError`, so that
  `python -m recval summarize RULES EMPTY_FILE` prints the 2-space
  indented JSON object
  `{"total": 0, "valid": 0, "invalid": 0, "errors_by_field": {}}`
  and exits 0.
- FAC06-7: Add a new `## 0.3.0` section at the top of CHANGELOG.md
  containing the bullet `- Added the summarize subcommand.`
- FAC06-10: Add `tests/test_summarize.py` with at least one unittest
  covering the summarize counts; `python -m unittest discover -s tests
  -v` must exit 0 and its output must mention `test_summarize`.
