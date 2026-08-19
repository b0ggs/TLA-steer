import unittest

from eventrollup.formatting import compact_json


class CompactJsonTests(unittest.TestCase):
    def test_compact_sorted_unicode_output(self):
        self.assertEqual(compact_json({"beta": "β", "alpha": 1}), '{"alpha":1,"beta":"β"}')


if __name__ == "__main__":
    unittest.main()
