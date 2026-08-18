# Serialized row format

## R6 — Configured quantity field

Change `config/fields.json` so `output_quantity_key` is `count`. `dump_rows(rows, output_path, config_path)` must read that setting and write a JSON array using the configured quantity key, followed by one newline.
