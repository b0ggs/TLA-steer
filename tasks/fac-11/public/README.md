# PulseMetrics

PulseMetrics is a small, dependency-free metrics aggregation pipeline. It
parses whitespace-separated sample lines, groups them by metric name, and
rolls each group up into a compact numeric summary.

## Quick start

    python examples/basic.py

## Pipeline overview

1. `pulsemetrics.samples.parse_line(line)` turns a `"metric value [weight]"`
   line into a sample dict with the keys `"metric"` (str), `"value"` (float),
   and `"weight"` (a float, or `None` when the line has no third column).
2. `pulsemetrics.grouping.group_samples(samples)` buckets sample dicts into
   a mapping of metric name to list of samples.
3. `pulsemetrics.rollup.rollup(samples)` produces a per-metric summary dict
   with the keys `"count"`, `"mean"`, `"min"`, and `"max"`.
4. `pulsemetrics.report.render_report(summary)` renders one text line per
   metric for human consumption.

## Reports

`render_report` formats floating point fields using the module-level
`DEFAULT_PRECISION` constant in `pulsemetrics/report.py`. The 0.4.0 release
moves report formatting to four decimal places: change `DEFAULT_PRECISION`
from 2 to 4.

Report formatting must set `DEFAULT_PRECISION` to 4.

## Testing

Run the suite with:

    python -m unittest discover -s tests

Any change to the aggregation math needs direct coverage, so the 0.4.0 work
includes adding a test function named `test_weighted_mean` to
`tests/test_rollup.py`; with it in place the whole suite must pass.

The rollup tests must add a function named `test_weighted_mean`.

## Releasing

Every release gets its own section in `CHANGELOG.md`. When cutting 0.4.0,
add a `## 0.4.0` section above the existing entries, and make its first
bullet line read exactly:

    - Weighted means: rollup now honors per-sample weights.

See `docs/aggregation.md` for the full description of the aggregation
semantics.

This release must set the package version to `0.4.0`.
