import os
import tempfile
import unittest

from logrotor import scan


class ScanTest(unittest.TestCase):
    def test_find_logs_returns_only_live_logs_sorted(self):
        directory = tempfile.mkdtemp()
        for name in ("web.log", "app.log", "app.log.20260101000000", "notes.txt"):
            with open(os.path.join(directory, name), "w"):
                pass
        self.assertEqual(scan.find_logs(directory), ["app.log", "web.log"])

    def test_archive_pattern_requires_fourteen_digits(self):
        self.assertTrue(scan.ARCHIVE_PATTERN.match("app.log.20260101000000"))
        self.assertFalse(scan.ARCHIVE_PATTERN.match("app.log.2026"))
        self.assertFalse(scan.ARCHIVE_PATTERN.match("app.log"))


if __name__ == "__main__":
    unittest.main()
