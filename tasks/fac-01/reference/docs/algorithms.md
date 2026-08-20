# colstat algorithms and output format

## Mean

The arithmetic mean of the column values. Documented example:
`mean([2.0, 4.0, 9.0])` returns `5.0`.

## Median

FAC01-1: For a column with an odd number of values, the median is the
middle value of the sorted list; documented example:
`median([5.0, 1.0, 9.0])` returns `5.0`. For a column with an even number
of values, the median must be the mean of the two middle values of the
sorted list; documented example: `median([1.0, 2.0, 3.0, 4.0])` must
return `2.5`.

FAC01-4: The docstring of `colstat.stats.median` must contain this line
verbatim:

    Returns the mean of the two middle values when n is even.

## Standard deviation

The population standard deviation, defined as `0.0` for fewer than two
values.

## Precision

FAC01-5: `colstat.config.DEFAULT_PRECISION` must be `4`. (Release 0.4.0
shipped with `6`; release 0.4.1 standardizes on four decimal places.)

## Input boundary

FAC01-6: `colstat.reader.load_rows` must raise `ValueError` with the
message exactly `no data rows in input` when the CSV file is empty or
contains only a header row.

## JSON output key order

FAC01-10: The JSON object printed by the `stats` command must contain its
keys in exactly this order: `count`, `min`, `max`, `mean`, `median`,
`stdev`.
