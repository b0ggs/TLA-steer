import unittest

from recval.summary import summarize_records

RULES = {
    "required": ["id", "name"],
    "types": {"id": "int", "age": "int"},
    "ranges": {"age": [0, 130]},
}


class TestSummarize(unittest.TestCase):
    def test_summarize_counts(self):
        records = [
            (1, {"id": 1, "name": "Ada", "age": 36}),
            (2, {"id": 2, "age": 29}),
            (3, {"id": 3, "name": "Alan", "age": 200}),
        ]
        summary = summarize_records(records, RULES)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["valid"], 1)
        self.assertEqual(summary["invalid"], 2)
        self.assertEqual(summary["errors_by_field"], {"age": 1, "name": 1})

    def test_empty_records(self):
        self.assertEqual(
            summarize_records([], RULES),
            {"total": 0, "valid": 0, "invalid": 0, "errors_by_field": {}},
        )


if __name__ == "__main__":
    unittest.main()
