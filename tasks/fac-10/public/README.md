# addrbook

A tiny, stdlib-only address-book normalizer and deduplicator.

```python
from addrbook import pipeline

unique = pipeline.run([
    {"name": "Ada  Lovelace", "email": " Ada.L@Example.COM ", "phones": ["(555) 123-4567"]},
    {"name": "ada lovelace", "email": "ada.l@example.com", "phones": []},
])
```

## Modules

- `addrbook.normalize` — per-record cleanup (`clean_name`, `normalize_email`,
  `normalize_record`).
- `addrbook.phones` — phone-number cleanup (`normalize_phone`).
- `addrbook.dedupe` — first-occurrence-wins deduplication, with an optional
  strict mode that raises `addrbook.errors.DuplicateKeyError`.
- `addrbook.pipeline` — `run(records)` = normalize then dedupe.
- `addrbook.config` — shared defaults (`DEFAULTS`).

## Documented behavior (must keep working)

- Emails are lowercased and stripped of surrounding whitespace:
  `normalize_email("  Ada.L@Example.COM ")` returns `"ada.l@example.com"`.
- Names have runs of whitespace collapsed to single spaces.
- Deduplication keeps the first record seen for each key value
  (default key: `email`).

## Demo

Run `python examples/run_demo.py`. It prints one line per unique contact and
ends by printing the line `3 unique contacts`. That final line must keep
printing exactly as-is.

## Release acceptance notes (1.4.0)

- FAC10-1: `normalize_phone` must return canonical NANP form for inputs whose
  digits form a 10-digit number: `normalize_phone("(555) 123-4567")` must
  return `"+1-555-123-4567"`, and `normalize_phone("555.867.5309")` must
  return `"+1-555-867-5309"`.
- FAC10-2: 11-digit inputs whose digits start with `1` drop that leading `1`
  and use the same canonical form: `normalize_phone("1 (555) 010-9999")` must
  return `"+1-555-010-9999"`. Inputs of any other digit length keep the
  existing digits-only behavior.
- FAC10-5: bump `addrbook.__version__` in `addrbook/__init__.py` to exactly
  `"1.4.0"`.

Further acceptance notes for this release are tagged FAC10-* in
`docs/normalization.md`, `CHANGELOG.md`, `tests/test_normalize.py`, and
`tests/test_dedupe.py`.
