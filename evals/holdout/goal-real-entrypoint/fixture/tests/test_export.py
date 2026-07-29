import json
import unittest

from sample_export import format_export


class ExportTests(unittest.TestCase):
    def test_json_format(self):
        self.assertEqual(
            {"count": 2, "items": ["alpha", "beta"]},
            json.loads(format_export("json")),
        )

    def test_text_format(self):
        self.assertEqual("alpha\nbeta", format_export("text"))


if __name__ == "__main__":
    unittest.main()
