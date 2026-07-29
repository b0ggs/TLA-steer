import unittest

from src.duration import display_duration


class DurationTests(unittest.TestCase):
    def test_existing_minute_display(self):
        self.assertEqual("5 min", display_duration(5))
        self.assertEqual("65 min", display_duration(65))


if __name__ == "__main__":
    unittest.main()
