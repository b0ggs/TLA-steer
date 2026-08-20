import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from addrbook import normalize

# FAC10-9: clean_name must treat every kind of whitespace (spaces, tabs,
# newlines) as a separator: clean_name("\t Ada \t Lovelace \n") must return
# "Ada Lovelace", and a name that is only whitespace, such as " \t ", must
# return "" (the empty string).


class TestNormalize(unittest.TestCase):
    def test_email_lowercased_and_stripped(self):
        self.assertEqual(
            normalize.normalize_email("  Ada.L@Example.COM "), "ada.l@example.com"
        )

    def test_clean_name_collapses_spaces(self):
        self.assertEqual(normalize.clean_name("Ada   Lovelace"), "Ada Lovelace")

    def test_clean_name_collapses_all_whitespace(self):
        self.assertEqual(
            normalize.clean_name("\t Ada \t Lovelace \n"), "Ada Lovelace"
        )
        self.assertEqual(normalize.clean_name(" \t "), "")

    def test_normalize_record_does_not_mutate_input(self):
        original = {
            "name": "Ada   Lovelace",
            "email": " Ada@Example.COM ",
            "phones": ["(555) 123-4567"],
        }
        snapshot = {**original, "phones": list(original["phones"])}
        result = normalize.normalize_record(original)
        self.assertIsNot(result, original)
        self.assertEqual(original, snapshot)
        result["phones"].append("extra")
        self.assertEqual(original, snapshot)


if __name__ == "__main__":
    unittest.main()
