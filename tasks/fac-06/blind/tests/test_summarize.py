import unittest

from recval.engine import summarize_records


RULES = {
    "required": ["id", "name"],
    "types": {"id": "int", "name": "str", "age": "int"},
    "ranges": {"age": [0, 130]},
}


class TestSummarize(unittest.TestCase):
    def test_summarize_counts(self):
        records = [
            (1, {"id": 1, "name": "Ada", "age": 36}),
            (2, {"id": 2, "age": 45}),
            (3, {"id": 3, "name": "Grace", "age": 200}),
        ]
        self.assertEqual(
            summarize_records(records, RULES),
            {
                "total": 3,
                "valid": 1,
                "invalid": 2,
                "errors_by_field": {"age": 1, "name": 1},
            },
        )

    def test_summarize_empty_records(self):
        self.assertEqual(
            summarize_records([], RULES),
            {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "errors_by_field": {},
            },
        )


if __name__ == "__main__":
    unittest.main()
