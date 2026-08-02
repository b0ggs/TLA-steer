import unittest

import delivery


class DeliveryPublicTests(unittest.TestCase):
    def test_records_are_fresh_and_stable(self) -> None:
        first = delivery.delivery_records()
        first[0]["weight"] = 99
        self.assertEqual(delivery.delivery_records()[0]["weight"], 2)

    def test_rates_are_stable(self) -> None:
        self.assertEqual(delivery.zone_rates(), {"east": 4, "west": 3})

    def test_supported_shipping_cost_uses_zone_rate(self) -> None:
        item = {"delivery_id": "D-1", "zone": "east", "weight": 3}
        self.assertEqual(delivery.shipping_cost(item, {"east": 4}), 12)
        with self.assertRaises(KeyError):
            delivery.shipping_cost(item, {})


if __name__ == "__main__":
    unittest.main()
