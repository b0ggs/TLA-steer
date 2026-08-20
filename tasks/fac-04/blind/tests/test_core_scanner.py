import unittest

from tocsmith.scanner import scan_text

DOC = """# Title

```py
# comment, not a heading
```

## Section

### Sub
"""


class ScannerTest(unittest.TestCase):
    def test_levels_titles_lines(self):
        headings = scan_text(DOC)
        self.assertEqual(
            [(h.level, h.title, h.line) for h in headings],
            [(1, "Title", 1), (2, "Section", 7), (3, "Sub", 9)],
        )

    def test_fenced_code_is_skipped(self):
        titles = [h.title for h in scan_text(DOC)]
        self.assertNotIn("comment, not a heading", titles)

    def test_requires_space_after_hashes(self):
        self.assertEqual(scan_text("#NoSpace\n"), [])


if __name__ == "__main__":
    unittest.main()
