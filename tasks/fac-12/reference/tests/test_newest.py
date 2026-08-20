import os
import tempfile
import unittest
from pathlib import Path

from dirlens.report import newest_entries, newest_lines

BASE = 1_700_000_000


class NewestTests(unittest.TestCase):
    def _build_tree(self, root):
        for offset, name in enumerate(["old.txt", "mid.txt", "new.txt"]):
            path = root / name
            path.write_text(name)
            os.utime(path, (BASE + offset, BASE + offset))

    def test_newest_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._build_tree(root)
            lines = newest_lines(root, 2)
            self.assertEqual(len(lines), 2)
            self.assertTrue(lines[0].endswith("\tnew.txt"))
            self.assertTrue(lines[1].endswith("\tmid.txt"))

    def test_newest_entry_keys_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._build_tree(root)
            entries = newest_entries(root, 5)
            self.assertEqual(
                [entry["path"] for entry in entries],
                ["new.txt", "mid.txt", "old.txt"],
            )
            for entry in entries:
                self.assertEqual(sorted(entry), ["mtime", "path"])

    def test_newest_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(newest_lines(Path(tmp), 5), [])
            self.assertEqual(newest_entries(Path(tmp), 5), [])


if __name__ == "__main__":
    unittest.main()
