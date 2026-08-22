import unittest

from urllib.parse import urljoin


class RelativeBaseTests(unittest.TestCase):
    def test_undefined_authority_base(self):
        self.assertEqual(urljoin("//", "w"), "///w")
        self.assertEqual(urljoin("//", "/w"), "///w")
        self.assertEqual(urljoin("//a", "w"), "//a/w")

    def test_relative_path_base(self):
        self.assertEqual(urljoin("/b/c", "w"), "/b/w")
        self.assertEqual(urljoin("///b/c", "w"), "///b/w")


if __name__ == "__main__":
    unittest.main()
