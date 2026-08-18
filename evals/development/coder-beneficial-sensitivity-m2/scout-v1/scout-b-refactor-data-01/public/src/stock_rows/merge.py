"""Row merging.

R5 — Duplicate-SKU transformation

`merge_rows(rows)` must combine repeated SKUs by summing quantities, return one row per SKU in first-occurrence SKU order, and keep the labels tuple from the first row for each SKU.
"""


def merge_rows(rows):
    return list(rows)
