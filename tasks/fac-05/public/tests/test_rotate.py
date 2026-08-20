import os
import tempfile
import unittest

from logrotor import rotate


class RotateTest(unittest.TestCase):
    def test_rotate_directory_archives_and_recreates(self):
        directory = tempfile.mkdtemp()
        path = os.path.join(directory, "app.log")
        with open(path, "w") as fh:
            fh.write("one line\n")
        rotated = rotate.rotate_directory(directory)
        self.assertEqual(len(rotated), 1)
        name, archive = rotated[0]
        self.assertEqual(name, "app.log")
        self.assertTrue(archive.startswith("app.log."))
        self.assertTrue(os.path.exists(os.path.join(directory, archive)))
        self.assertEqual(os.path.getsize(path), 0)

    def test_timestamp_is_fourteen_digits(self):
        stamp = rotate.timestamp()
        self.assertEqual(len(stamp), 14)
        self.assertTrue(stamp.isdigit())


if __name__ == "__main__":
    unittest.main()
