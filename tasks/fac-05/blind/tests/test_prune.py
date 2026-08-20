import os
import tempfile
import unittest

from logrotor import prune, scan


class PruneTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

    def _touch(self, name):
        with open(os.path.join(self.directory, name), "w"):
            pass

    def test_prune_keeps_newest_archives_per_log(self):
        for name in (
            "app.log.20260301090000",
            "app.log.20260302090000",
            "app.log.20260303090000",
            "web.log.20260301090000",
            "web.log.20260302090000",
            "web.log",
            "notes.txt",
        ):
            self._touch(name)

        self.assertEqual(
            prune.prune_directory(self.directory, keep=1),
            [
                "app.log.20260301090000",
                "app.log.20260302090000",
                "web.log.20260301090000",
            ],
        )
        self.assertEqual(
            scan.find_archives(self.directory),
            ["app.log.20260303090000", "web.log.20260302090000"],
        )
        self.assertTrue(os.path.exists(os.path.join(self.directory, "web.log")))
        self.assertTrue(os.path.exists(os.path.join(self.directory, "notes.txt")))

    def test_dry_run_reports_without_deleting(self):
        for name in (
            "app.log.20260301090000",
            "app.log.20260302090000",
        ):
            self._touch(name)
        self.assertEqual(
            prune.prune_directory(self.directory, keep=1, dry_run=True),
            ["app.log.20260301090000"],
        )
        self.assertEqual(len(scan.find_archives(self.directory)), 2)

    def test_empty_directory_has_no_archives(self):
        self.assertEqual(scan.find_archives(self.directory), [])


if __name__ == "__main__":
    unittest.main()
