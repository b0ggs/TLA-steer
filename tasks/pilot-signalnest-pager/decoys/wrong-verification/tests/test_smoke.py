import unittest

from signalnest import UnknownRoute, resolve_route


class SmokeTests(unittest.TestCase):
    def test_existing_aliases(self):
        self.assertEqual(resolve_route("email"), "standard")
        self.assertEqual(resolve_route("SMS"), "mobile")

    def test_unknown_alias(self):
        with self.assertRaises(UnknownRoute):
            resolve_route("carrier-pigeon")


if __name__ == "__main__":
    unittest.main()
