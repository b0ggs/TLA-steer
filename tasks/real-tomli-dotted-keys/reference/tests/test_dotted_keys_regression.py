import unittest

import tomli


class DottedKeyNamespaceRegressionTests(unittest.TestCase):
    def test_rejects_extension_below_explicit_tables(self):
        cases = (
            "[a.b.c]\n  z = 9\n[a]\n  b.c.t = 9\n",
            "[a.b.c.d]\n  z = 9\n[a]\n  b.c.d.k.t = 8\n",
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(tomli.TOMLDecodeError):
                    tomli.loads(source)

    def test_rejects_extension_below_array_of_tables(self):
        source = "[[tab.arr]]\n[tab]\narr.val1=1\n"
        with self.assertRaises(tomli.TOMLDecodeError):
            tomli.loads(source)


if __name__ == "__main__":
    unittest.main()

