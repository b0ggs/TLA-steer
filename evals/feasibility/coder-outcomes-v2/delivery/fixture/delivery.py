from __future__ import annotations

from typing import Any


def delivery_records() -> list[dict[str, Any]]:
    return [
        {"delivery_id": "D-200", "zone": "west", "weight": 2},
        {"delivery_id": "D-100", "zone": "east", "weight": 3},
    ]


def zone_rates() -> dict[str, int]:
    return {"east": 4, "west": 3}


def shipping_cost(delivery: dict[str, Any], rates: dict[str, int]) -> int:
    return delivery["weight"] * rates[delivery["zone"]]


def legacy_quote(delivery: dict[str, Any], rates: dict[str, int]) -> int:
    return shipping_cost(delivery, rates)
