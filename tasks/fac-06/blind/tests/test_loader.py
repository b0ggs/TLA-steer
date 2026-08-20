import os
import tempfile
import unittest

from recval.loader import LoaderError, iter_records


class TestIterRecords(unittest.TestCase):
    def _write(self, text):
        handle, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(handle, "w", encoding="utf-8") as fh:
            fh.write(text)
        self.addCleanup(os.remove, path)
        return path

    def test_reads_records_with_line_numbers(self):
        path = self._write('{"id": 1}\n\n{"id": 2}\n')
        self.assertEqual(iter_records(path), [(1, {"id": 1}), (3, {"id": 2})])

    def test_rejects_non_object_lines(self):
        path = self._write("[1, 2]\n")
        with self.assertRaises(LoaderError):
            iter_records(path)


if __name__ == "__main__":
    unittest.main()
