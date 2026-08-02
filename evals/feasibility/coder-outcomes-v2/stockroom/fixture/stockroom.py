from __future__ import annotations


class Stockroom:
    def __init__(self, stock: dict[str, int]) -> None:
        if any(quantity < 0 for quantity in stock.values()):
            raise ValueError("stock quantities must be non-negative")
        self._stock = dict(stock)

    def available(self, sku: str) -> int:
        return self._stock.get(sku, 0)

    def reserve(self, sku: str, quantity: int) -> bool:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        current = self._stock.get(sku, 0)
        self._stock[sku] = max(0, current - quantity)
        return current >= quantity

    def snapshot(self) -> dict[str, int]:
        return dict(self._stock)
