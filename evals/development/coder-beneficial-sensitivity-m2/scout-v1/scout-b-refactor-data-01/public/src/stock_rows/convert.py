"""Mapping conversion.

R2 — Legacy quantity alias

`row_from_mapping(data)` must accept legacy mappings that provide `qty` when `quantity` is absent; if `quantity` is present it remains the selected value.

R3 — Input integrity

`row_from_mapping(data)` must return labels as a sorted tuple without changing the input mapping or its labels list.

R4 — Quantity boundary

`row_from_mapping(data)` must raise `ValueError` when the selected quantity is a negative integer; zero remains valid.
"""

from .model import InventoryRow


def row_from_mapping(data):
    quantity = int(data["quantity"])
    labels = data.get("labels", [])
    labels.sort()
    return InventoryRow(str(data["sku"]), quantity, tuple(labels))


def row_to_mapping(row, *, quantity_key="quantity"):
    return {
        "sku": row.sku,
        quantity_key: row.quantity,
        "labels": list(row.labels),
    }
