# Stock rows

The package converts inventory mappings, merges rows, and writes JSON.

## Compatibility

G1 — `row_to_mapping(row)` without a `quantity_key` argument must remain compatible by emitting the key `quantity` and a list-valued `labels` field.
