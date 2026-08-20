# Example inputs

- `rules.json` — the schema-lite rules file used throughout the docs.
- `records.jsonl` — six records; records 3 and 5 are invalid.
- `valid_only.jsonl` — three records that all pass the rules.

Acceptance notes:

- FAC06-6: Add `examples/summary.json` holding exactly the JSON summary
  object that
  `python -m recval summarize examples/rules.json examples/records.jsonl`
  prints (see FAC06-2 in docs/cli.md for the exact object).
