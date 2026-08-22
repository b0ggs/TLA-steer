import unittest

from signalnest import resolve_route


class RouteCases(unittest.TestCase):
    def test_pager_route(self):
        self.assertEqual(resolve_route("pager"), "urgent")

    def test_pager_route_normalization(self):
        for value in ("PAGER", " pager", "pager ", "  PaGeR  "):
            with self.subTest(value=value):
                self.assertEqual(resolve_route(value), "urgent")


if __name__ == "__main__":
    unittest.main()
