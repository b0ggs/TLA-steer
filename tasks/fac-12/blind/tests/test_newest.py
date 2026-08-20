import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from dirlens.cli import main
from dirlens.report import newest_entries, newest_lines


class NewestTests(unittest.TestCase):
    def test_newest_orders_by_time_then_path_and_honors_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            older = root / "older.txt"
            alpha = root / "alpha.txt"
            beta = root / "beta.txt"
            for path in (older, alpha, beta):
                path.write_text(path.name, encoding="utf-8")
            os.utime(older, (1_600_000_000, 1_600_000_000))
            os.utime(alpha, (1_700_000_000, 1_700_000_000))
            os.utime(beta, (1_700_000_000, 1_700_000_000))

            self.assertEqual(
                newest_lines(root, limit=2),
                [
                    "2023-11-14T22:13:20Z\talpha.txt",
                    "2023-11-14T22:13:20Z\tbeta.txt",
                ],
            )

    def test_json_mode_for_empty_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = main(["newest", tmp, "--json"])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(stdout.getvalue()), [])
            self.assertEqual(newest_entries(tmp), [])


if __name__ == "__main__":
    unittest.main()
