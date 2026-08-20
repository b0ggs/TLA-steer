import unittest

from tocsmith.scanner import scan_text
from tocsmith.toc import build_entries


class JsonEntriesTest(unittest.TestCase):
    def test_json_entries_for_sample(self):
        with open("examples/sample.md", "r", encoding="utf-8") as fh:
            text = fh.read()
        entries = build_entries(scan_text(text))
        self.assertEqual(
            entries,
            [
                {"level": 1, "title": "Tocsmith Sample", "anchor": "tocsmith-sample", "line": 1},
                {"level": 2, "title": "Getting Started", "anchor": "getting-started", "line": 5},
                {"level": 3, "title": "Install", "anchor": "install", "line": 7},
                {"level": 2, "title": "Usage", "anchor": "usage", "line": 15},
                {"level": 3, "title": "Install", "anchor": "install-1", "line": 17},
            ],
        )


if __name__ == "__main__":
    unittest.main()
