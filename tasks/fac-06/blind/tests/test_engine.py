import unittest

from recval.engine import check_record

RULES = {
    "required": ["id", "name"],
    "types": {"id": "int", "name": "str", "age": "int"},
    "ranges": {"age": [0, 130]},
}


class TestCheckRecord(unittest.TestCase):
    def test_valid_record(self):
        self.assertEqual(
            check_record({"id": 1, "name": "Ada", "age": 36}, RULES), []
        )

    def test_missing_required_key(self):
        self.assertEqual(
            check_record({"id": 1}, RULES), [("name", "missing required key")]
        )

    def test_type_mismatch(self):
        self.assertEqual(
            check_record({"id": "x", "name": "Ada"}, RULES),
            [("id", "expected int")],
        )

    def test_out_of_range(self):
        self.assertEqual(
            check_record({"id": 1, "name": "Ada", "age": 200}, RULES),
            [("age", "out of range 0..130")],
        )


if __name__ == "__main__":
    unittest.main()
