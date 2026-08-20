import os
import tempfile
import unittest

from logrotor import prune


class PruneTest(unittest.TestCase):
    def test_keeps_newest_archives_per_log(self):
        directory = tempfile.mkdtemp()
        app = [
            "app.log.20260101000000",
            "app.log.20260102000000",
            "app.log.20260103000000",
        ]
        web = ["web.log.20260101000000", "web.log.20260102000000"]
        for name in app + web:
            with open(os.path.join(directory, name), "w"):
                pass
        doomed = prune.prune_directory(directory, keep=2)
        self.assertEqual(doomed, ["app.log.20260101000000"])
        self.assertEqual(sorted(os.listdir(directory)), sorted(app[1:] + web))

    def test_dry_run_deletes_nothing(self):
        directory = tempfile.mkdtemp()
        names = ["app.log.20260101000000", "app.log.20260102000000"]
        for name in names:
            with open(os.path.join(directory, name), "w"):
                pass
        doomed = prune.prune_directory(directory, keep=1, dry_run=True)
        self.assertEqual(doomed, ["app.log.20260101000000"])
        self.assertEqual(sorted(os.listdir(directory)), names)

    def test_empty_directory_prunes_nothing(self):
        directory = tempfile.mkdtemp()
        self.assertEqual(prune.prune_directory(directory, keep=5), [])


if __name__ == "__main__":
    unittest.main()
