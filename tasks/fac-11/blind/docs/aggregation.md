# Aggregation semantics

This document describes what each stage of the pipeline guarantees.

## Grouping

`group_samples` walks the input list once and buckets each sample dict by
its `"metric"` key, preserving the first-seen order of samples inside each
bucket. As part of the 0.4.0 hardening, `group_samples` in
`pulsemetrics/grouping.py` must reject a sample that has no `"metric"` key
by raising `ValueError` with the message `sample is missing a metric name`
(that exact wording).

## Rollup

`rollup` composes grouping with per-group statistics. Each summary carries
`"count"`, `"mean"`, `"min"`, and `"max"`; 0.4.0 adds `"weight_total"` as
described in the issue. Starting with 0.4.0, the mapping returned by
`rollup` must list its metric names in ascending alphabetical order rather
than in first-seen order.

Because the weight default is easy to miss when reading the code, the
docstring of `rollup` must include the sentence
`Weights default to 1.0 when a sample omits them.` so that `help(rollup)`
states it plainly.

## Statistics helpers

`pulsemetrics/stats.py` hosts the pure numeric helpers (`mean_value` and
`median_value`). They operate on plain lists of floats and know nothing
about sample dicts, which keeps them easy to test in isolation.
