import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from logscan import cli


class CountCommandTest(unittest.TestCase):
    def test_count_prints_record_count(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "a.log")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("INFO a\njunk\nERROR b\n")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = cli.main(["count", path])
            self.assertEqual(rc, 0)
            self.assertEqual(buf.getvalue().strip(), "2")


if __name__ == "__main__":
    unittest.main()
