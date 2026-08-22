import doctest
import textwrap
import unittest


class DoctestNotesRegressionTests(unittest.TestCase):
    def run_doctest(self, source):
        source = textwrap.dedent(source).lstrip()
        test = doctest.DocTestParser().get_doctest(
            source, {}, "exception-notes", "exception-notes", 0
        )
        return doctest.DocTestRunner(verbose=False).run(test, out=lambda _: None)

    def assert_doctest_passes(self, source):
        result = self.run_doctest(source)
        self.assertEqual(result.failed, 0)

    def test_exception_with_note(self):
        self.assert_doctest_passes(
            """
            >>> exc = ValueError('Text')
            >>> exc.add_note('Note')
            >>> raise exc
            Traceback (most recent call last):
              ...
            ValueError: Text
            Note
            """
        )

    def test_exception_with_multiple_notes(self):
        self.assert_doctest_passes(
            """
            >>> exc = ValueError('Text')
            >>> exc.add_note('One')
            >>> exc.add_note('Two')
            >>> raise exc
            Traceback (most recent call last):
              ...
            ValueError: Text
            One
            Two
            """
        )

    def test_syntax_error_with_note(self):
        self.assert_doctest_passes(
            """
            >>> exc = SyntaxError('error', ('x.py', 23, None, 'bad syntax'))
            >>> exc.add_note('Note')
            >>> raise exc
            Traceback (most recent call last):
              ...
            SyntaxError: error
            Note
            """
        )

    def test_incorrect_note_fails(self):
        result = self.run_doctest(
            """
            >>> exc = ValueError('Text')
            >>> exc.add_note('actual note')
            >>> raise exc
            Traceback (most recent call last):
              ...
            ValueError: Text
            wrong note
            """
        )
        self.assertEqual(result.failed, 1)

    def test_exception_without_note_still_passes(self):
        self.assert_doctest_passes(
            """
            >>> raise ValueError('Text')
            Traceback (most recent call last):
              ...
            ValueError: Text
            """
        )

    def test_plain_output_still_passes(self):
        self.assert_doctest_passes(
            """
            >>> print('unchanged')
            unchanged
            """
        )


if __name__ == "__main__":
    unittest.main()
