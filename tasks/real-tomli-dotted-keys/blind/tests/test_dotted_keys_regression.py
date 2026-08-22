import unittest

import tomli


class DottedKeysRegressionTest(unittest.TestCase):
    def test_dotted_key_cannot_extend_explicit_table(self) -> None:
        source = """
            [fruit.apple]
            [fruit]
            apple.color = "red"
        """

        with self.assertRaises(tomli.TOMLDecodeError):
            tomli.loads(source)

    def test_dotted_key_cannot_extend_array_of_tables(self) -> None:
        source = """
            [[fruit.apple]]
            [fruit]
            apple.color = "red"
        """

        with self.assertRaises(tomli.TOMLDecodeError):
            tomli.loads(source)


if __name__ == "__main__":
    unittest.main()
