# Changelog

## Unreleased

The next release will be 0.4.0, and `__version__` in
`pulsemetrics/__init__.py` should be bumped to `0.4.0` to match it. Also
planned for that release: `parse_line` in `pulsemetrics/samples.py` will
strip leading and trailing whitespace from a line before splitting it, so
that `"  cpu.load 1.5 "` parses to metric `cpu.load`, value 1.5, and no
weight (`"weight"` is `None`).

The 0.4.0 changelog must document that rollup honors per-sample weights.

## 0.3.1

- Fixed median_value for even-length inputs.

## 0.3.0

- Added render_report.

## 0.2.0

- Initial grouping and rollup pipeline.
