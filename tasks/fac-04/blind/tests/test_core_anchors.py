import unittest

from tocsmith.anchors import AnchorRegistry, slugify


class SlugifyTest(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(slugify("Getting Started"), "getting-started")

    def test_punctuation_dropped(self):
        self.assertEqual(slugify("What's New?"), "whats-new")


class RegistryTest(unittest.TestCase):
    def test_duplicates_numbered(self):
        registry = AnchorRegistry()
        self.assertEqual(registry.anchor_for("Install"), "install")
        self.assertEqual(registry.anchor_for("Install"), "install-1")
        self.assertEqual(registry.anchor_for("Install"), "install-2")


if __name__ == "__main__":
    unittest.main()
