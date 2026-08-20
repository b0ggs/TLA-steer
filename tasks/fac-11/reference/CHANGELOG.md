# Changelog

## Unreleased

Nothing yet.

## 0.4.0

- Weighted means: rollup now honors per-sample weights.
- Rollup summaries gained a weight_total key and list metrics alphabetically.
- Bumped __version__ to 0.4.0.
- parse_line strips surrounding whitespace before splitting.
- group_samples rejects samples without a metric name with a ValueError.
- mean_value returns 0.0 for an empty list.
- Reports render with four decimal places by default.

## 0.3.1

- Fixed median_value for even-length inputs.

## 0.3.0

- Added render_report.

## 0.2.0

- Initial grouping and rollup pipeline.
