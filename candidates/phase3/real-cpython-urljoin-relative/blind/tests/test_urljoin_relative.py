import sys
import unittest
from pathlib import Path


# Running this file directly puts tests/ rather than the repository root first
# on sys.path.  Some test runners also import the host Python's urllib during
# startup, so discard that copy before importing the implementation under test.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for module_name in tuple(sys.modules):
    if module_name == "urllib" or module_name.startswith("urllib."):
        del sys.modules[module_name]

from urllib.parse import urljoin


class UrlJoinRelativeTests(unittest.TestCase):
    def test_required_relative_bases(self):
        cases = (
            ("", "w", "w"),
            ("/", "w", "/w"),
            ("//", "w", "///w"),
            ("//", "/w", "///w"),
            ("//a", "w", "//a/w"),
            ("http:", "w", "http:/w"),
            ("http://", "w", "http:///w"),
            ("http://a", "w", "http://a/w"),
            ("/b/c", "w", "/b/w"),
            ("b/c", "w", "b/w"),
            ("///b/c", "w", "///b/w"),
        )

        for base, reference, expected in cases:
            with self.subTest(base=base, reference=reference):
                self.assertEqual(urljoin(base, reference), expected)

    def test_empty_reference_preserves_base(self):
        for base in (
            "//", "//a", "http:", "http://", "http://a", "/b/c", "///b/c"
        ):
            with self.subTest(base=base):
                self.assertEqual(urljoin(base, ""), base)

    def test_slash_only_references_preserve_authority_semantics(self):
        cases = {
            "//": ("///", "//", "///"),
            "//a": ("//a/", "//", "///"),
            "http:": ("http:/", "http://", "http:///"),
            "http://": ("http:///", "http://", "http:///"),
            "http://a": ("http://a/", "http://", "http:///"),
            "/b/c": ("/", "//", "///"),
            "///b/c": ("///", "//", "///"),
        }

        for base, expected_results in cases.items():
            for reference, expected in zip(("/", "//", "///"), expected_results):
                with self.subTest(base=base, reference=reference):
                    self.assertEqual(urljoin(base, reference), expected)

    def test_explicit_authority_replaces_base_authority(self):
        for base in (
            "//", "//a", "http:", "http://", "http://a", "/b/c", "///b/c"
        ):
            scheme = "http:" if base.startswith("http:") else ""
            with self.subTest(base=base, reference="//w"):
                self.assertEqual(urljoin(base, "//w"), f"{scheme}//w")
            with self.subTest(base=base, reference="//"):
                self.assertEqual(urljoin(base, "//"), f"{scheme}//")

    def test_bytes_preserve_relative_base_components(self):
        self.assertEqual(urljoin(b"//", b"w"), b"///w")
        self.assertEqual(urljoin(b"/b/c", b"w"), b"/b/w")


if __name__ == "__main__":
    unittest.main()
