"""Regression tests for doctest exception-note comparisons."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tested_doctest", ROOT / "doctest.py")
doctest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(doctest)


def raise_with_notes(exception, *notes):
    for note in notes:
        exception.add_note(note)
    raise exception


def raise_syntax_error_with_notes(exception_type, *notes):
    exception = exception_type(
        "bad syntax", ("actual.py", 2, 4, "x = )\n")
    )
    raise_with_notes(exception, *notes)


class ExceptionNotesRegressionTests(unittest.TestCase):
    def run_doctest(self, source):
        test = doctest.DocTestParser().get_doctest(
            source,
            {
                "raise_with_notes": raise_with_notes,
                "raise_syntax_error_with_notes": raise_syntax_error_with_notes,
                "SyntaxError": SyntaxError,
                "IndentationError": IndentationError,
                "TabError": TabError,
                "ValueError": ValueError,
            },
            "exception_notes",
            __file__,
            0,
        )
        output = []
        result = doctest.DocTestRunner().run(test, out=output.append)
        return result, "".join(output)

    def assert_doctest_passes(self, source):
        result, output = self.run_doctest(source)
        self.assertEqual(result.attempted, 1)
        self.assertEqual(result.failed, 0, output)

    def test_ordinary_exception_note(self):
        self.assert_doctest_passes(
            '''
            >>> raise_with_notes(ValueError("bad value"), "check the input")
            Traceback (most recent call last):
            ValueError: bad value
            check the input
            '''
        )

    def test_multiple_exception_notes(self):
        self.assert_doctest_passes(
            '''
            >>> raise_with_notes(ValueError("bad value"), "first note", "second note")
            Traceback (most recent call last):
            ValueError: bad value
            first note
            second note
            '''
        )

    def test_syntax_error_family_notes_ignore_source_location(self):
        for exception_type in (SyntaxError, IndentationError, TabError):
            with self.subTest(exception_type=exception_type.__name__):
                self.assert_doctest_passes(
                    f'''
                    >>> raise_syntax_error_with_notes({exception_type.__name__}, "first note\\ncontinued", "second note")
                    Traceback (most recent call last):
                      File "ignored.py", line 999
                        ignored source text
                        ^
                    {exception_type.__name__}: bad syntax
                    first note
                    continued
                    second note
                    '''
                )

    def test_incorrect_expected_note_fails(self):
        result, output = self.run_doctest(
            '''
            >>> raise_with_notes(ValueError("bad value"), "actual note")
            Traceback (most recent call last):
            ValueError: bad value
            incorrect note
            '''
        )
        self.assertEqual(result.attempted, 1)
        self.assertEqual(result.failed, 1)
        self.assertIn("actual note", output)

    def test_exception_without_notes_is_unchanged(self):
        self.assert_doctest_passes(
            '''
            >>> raise_with_notes(ValueError("bad value"))
            Traceback (most recent call last):
            ValueError: bad value
            '''
        )


if __name__ == "__main__":
    unittest.main()
