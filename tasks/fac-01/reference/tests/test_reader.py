"""Unit tests for colstat.reader."""

import os
import tempfile
import unittest

from colstat import reader


class ReaderTests(unittest.TestCase):
    def test_load_rows(self):
        workdir = tempfile.mkdtemp()
        path = os.path.join(workdir, "sample.csv")
        with open(path, "w", newline="") as handle:
            handle.write("name,score\na,1.5\nb,2.5\n")
        header, data_rows = reader.load_rows(path)
        self.assertEqual(header, ["name", "score"])
        self.assertEqual(data_rows, [["a", "1.5"], ["b", "2.5"]])

    def test_column(self):
        header = ["name", "score"]
        data_rows = [["a", "1.5"], ["b", "2.5"]]
        self.assertEqual(reader.column(header, data_rows, "score"), [1.5, 2.5])

    def test_unknown_column(self):
        with self.assertRaises(LookupError):
            reader.column(["name"], [], "score")


if __name__ == "__main__":
    unittest.main()
