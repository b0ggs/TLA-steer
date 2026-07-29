import unittest

from src.statuses import status_for_error


class StatusTests(unittest.TestCase):
    def test_known_statuses(self):
        self.assertEqual(400, status_for_error("validation_error"))
        self.assertEqual(404, status_for_error("not_found"))
        self.assertEqual(409, status_for_error("conflict"))

    def test_unknown_status(self):
        self.assertEqual(500, status_for_error("unexpected"))


if __name__ == "__main__":
    unittest.main()
