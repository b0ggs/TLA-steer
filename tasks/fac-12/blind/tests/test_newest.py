import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from dirlens.cli import main
from dirlens.report import newest_entries


class NewestTests(unittest.TestCase):
    def make_tree(self, root):
        files = {
            "old.txt": 1_600_000_000,
            "same-b.txt": 1_700_000_000,
            "same-a.txt": 1_700_000_000,
            "new.txt": 1_800_000_000,
        }
        for name, mtime in files.items():
            path = root / name
            path.write_text(name)
            os.utime(path, (mtime, mtime))

    def test_newest_entries_orders_limits_and_formats(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_tree(root)

            self.assertEqual(
                newest_entries(root, 3),
                [
                    {"path": "new.txt", "mtime": "2027-01-15T08:00:00Z"},
                    {"path": "same-a.txt", "mtime": "2023-11-14T22:13:20Z"},
                    {"path": "same-b.txt", "mtime": "2023-11-14T22:13:20Z"},
                ],
            )

    def test_cli_defaults_to_five_plain_text_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for index in range(7):
                path = root / ("file-%d" % index)
                path.write_text("x")
                os.utime(path, (1_700_000_000 + index, 1_700_000_000 + index))

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(["newest", str(root)])

            self.assertEqual(result, 0)
            lines = stdout.getvalue().splitlines()
            self.assertEqual(len(lines), 5)
            self.assertTrue(lines[0].endswith("\tfile-6"))

    def test_json_and_empty_tree_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = main(["newest", tmp, "--json"])

            self.assertEqual(result, 0)
            self.assertEqual(json.loads(stdout.getvalue()), [])

    def test_missing_path_exits_with_status_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                result = main(["newest", str(missing)])

            self.assertEqual(result, 3)
            self.assertIn("path does not exist", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
