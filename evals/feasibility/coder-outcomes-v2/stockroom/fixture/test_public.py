import unittest

from stockroom import Stockroom


class StockroomPublicTests(unittest.TestCase):
    def test_lookup_and_snapshot_are_stable(self) -> None:
        room = Stockroom({"bolt": 5})
        snapshot = room.snapshot()
        snapshot["bolt"] = 0
        self.assertEqual(room.available("bolt"), 5)
        self.assertEqual(room.available("missing"), 0)

    def test_successful_reservation_decrements_stock(self) -> None:
        room = Stockroom({"bolt": 5})
        self.assertTrue(room.reserve("bolt", 2))
        self.assertEqual(room.available("bolt"), 3)

    def test_invalid_quantities_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Stockroom({"bolt": -1})
        room = Stockroom({"bolt": 5})
        with self.assertRaises(ValueError):
            room.reserve("bolt", 0)


if __name__ == "__main__":
    unittest.main()
