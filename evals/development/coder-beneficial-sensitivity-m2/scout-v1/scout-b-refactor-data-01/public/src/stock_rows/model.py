"""Inventory row representation."""


class InventoryRow:
    def __init__(self, sku, quantity, labels=()):
        self.sku = sku
        self.quantity = quantity
        self.labels = labels

    def __eq__(self, other):
        if not isinstance(other, InventoryRow):
            return NotImplemented
        return (
            self.sku,
            self.quantity,
            self.labels,
        ) == (
            other.sku,
            other.quantity,
            other.labels,
        )
