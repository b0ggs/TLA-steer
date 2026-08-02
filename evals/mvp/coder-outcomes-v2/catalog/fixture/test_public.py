import unittest

from catalog import canonical_sku, pages


class CatalogRegressionTests(unittest.TestCase):
    def test_sku_comparison_form(self):
        self.assertEqual(canonical_sku(" Ab-12 C "), "ab12c")
        self.assertEqual(canonical_sku(407), "407")

    def test_sequence_pages_keep_order_and_remainder(self):
        source = ["a", "b", "c", "d", "e"]
        self.assertEqual(list(pages(source, 2)),
                         [["a", "b"], ["c", "d"], ["e"]])
        self.assertEqual(source, ["a", "b", "c", "d", "e"])
        self.assertEqual(list(pages((), 3)), [])

    def test_non_positive_page_size_is_rejected_at_call_time(self):
        with self.assertRaises(ValueError):
            pages([1, 2], 0)
        with self.assertRaises(ValueError):
            pages([1, 2], -1)


if __name__ == "__main__":
    unittest.main()
