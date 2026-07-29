import unittest

from src.duration import display_duration


class DurationTests(unittest.TestCase):
    def test_sub_hour_display_is_unchanged(self):
        self.assertEqual("0 min", display_duration(0))
        self.assertEqual("59 min", display_duration(59))


if __name__ == "__main__":
    unittest.main()
