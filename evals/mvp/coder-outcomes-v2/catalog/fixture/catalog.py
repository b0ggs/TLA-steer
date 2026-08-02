"""Small product catalog used by the evaluation fixture."""


def canonical_sku(value):
    """Return the catalog's comparison form for a SKU."""
    return "".join(char.lower() for char in str(value) if char not in " -")


def pages(items, size):
    """Split a sequence into list pages."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [list(items[offset:offset + size])
            for offset in range(0, len(items), size)]


def availability_report(products, warehouse_rows):
    raise NotImplementedError("warehouse availability is not connected")
