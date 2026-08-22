import sys
import unittest

from urllib.parse import urljoin, urlsplit


class IssueTests(unittest.TestCase):
    def check(self, base, reference, expected):
        self.assertEqual(urljoin(base, reference), expected)

    def test_relative_bases_and_undefined_authorities(self):
        cases = (
            ("", "", ""), ("", "//", "//"), ("", "//v", "//v"),
            ("", "//v/w", "//v/w"), ("", "/w", "/w"),
            ("", "///w", "///w"), ("", "w", "w"),
            ("//", "", "//"), ("//", "//", "//"),
            ("//", "//v", "//v"), ("//", "//v/w", "//v/w"),
            ("//", "/w", "///w"), ("//", "///w", "///w"),
            ("//", "w", "///w"), ("//a", "", "//a"),
            ("//a", "//", "//a"), ("//a", "//v", "//v"),
            ("//a", "//v/w", "//v/w"), ("//a", "/w", "//a/w"),
            ("//a", "///w", "//a/w"), ("//a", "w", "//a/w"),
            ("/b/c", "", "/b/c"), ("/b/c", "//", "/b/c"),
            ("/b/c", "//v", "//v"), ("/b/c", "//v/w", "//v/w"),
            ("/b/c", "/w", "/w"), ("/b/c", "///w", "/w"),
            ("/b/c", "w", "/b/w"), ("///b/c", "", "///b/c"),
            ("///b/c", "//", "///b/c"), ("///b/c", "//v", "//v"),
            ("///b/c", "//v/w", "//v/w"), ("///b/c", "/w", "///w"),
            ("///b/c", "///w", "///w"), ("///b/c", "w", "///b/w"),
        )
        for base, reference, expected in cases:
            with self.subTest(base=base, reference=reference):
                self.check(base, reference, expected)

    def test_scheme_only_and_empty_authority_bases(self):
        for prefix in "", "http:":
            cases = (
                ("http:", prefix + "", "http:"),
                ("http:", prefix + "//", "http:"),
                ("http:", prefix + "//v", "http://v"),
                ("http:", prefix + "//v/w", "http://v/w"),
                ("http:", prefix + "/w", "http:/w"),
                ("http:", prefix + "///w", "http:/w"),
                ("http:", prefix + "w", "http:/w"),
                ("http://", prefix + "", "http://"),
                ("http://", prefix + "//", "http://"),
                ("http://", prefix + "//v", "http://v"),
                ("http://", prefix + "//v/w", "http://v/w"),
                ("http://", prefix + "/w", "http:///w"),
                ("http://", prefix + "///w", "http:///w"),
                ("http://", prefix + "w", "http:///w"),
                ("http://a", prefix + "", "http://a"),
                ("http://a", prefix + "//", "http://a"),
                ("http://a", prefix + "//v", "http://v"),
                ("http://a", prefix + "//v/w", "http://v/w"),
                ("http://a", prefix + "/w", "http://a/w"),
                ("http://a", prefix + "///w", "http://a/w"),
                ("http://a", prefix + "w", "http://a/w"),
            )
            for base, reference, expected in cases:
                with self.subTest(prefix=prefix, base=base, reference=reference):
                    self.check(base, reference, expected)


class RegressionTests(unittest.TestCase):
    def test_rfc_style_absolute_base(self):
        base = "http://a/b/c/d;p?q"
        self.assertEqual(urljoin(base, "g"), "http://a/b/c/g")
        self.assertEqual(urljoin(base, "../g"), "http://a/b/g")
        self.assertEqual(urljoin(base, "?y"), "http://a/b/c/d;p?y")

    def test_urlsplit_components(self):
        parsed = urlsplit("https://example.test:8443/a?b=c#d")
        self.assertEqual(
            (parsed.scheme, parsed.hostname, parsed.port, parsed.path),
            ("https", "example.test", 8443, "/a"),
        )


if __name__ == "__main__":
    group = {"issue": IssueTests, "regression": RegressionTests}[sys.argv[1]]
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(group)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(not result.wasSuccessful())
