import tempfile
import unittest
from pathlib import Path

from dirlens.report import ext_lines, scan_lines


class ScanTests(unittest.TestCase):
    def test_scan_lists_files_sorted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "b.txt").write_text("bb")
            sub = root / "sub"
            sub.mkdir()
            (sub / "a.log").write_text("aaaa")
            self.assertEqual(scan_lines(root), ["b.txt\t2", "sub/a.log\t4"])

    def test_ext_counts_group_missing_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.txt").write_text("1")
            (root / "two.txt").write_text("2")
            (root / "plain").write_text("3")
            self.assertEqual(ext_lines(root), ["(none)\t1", "txt\t2"])


if __name__ == "__main__":
    unittest.main()
