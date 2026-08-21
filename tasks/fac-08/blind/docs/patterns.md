# Pattern syntax

pathsieve understands a deliberately small subset of the `.gitignore`
language. A rule set is a sequence of lines; each line is a blank line,
a comment, or a pattern.

## Blank lines and comments

Blank lines are skipped. A line whose first non-blank character is `#`
is a comment: leading spaces or tabs before the `#` do not stop a line
from being a comment, and a comment produces no rule at all. The loader
currently only recognises comments that start flush at column one,
which is a bug that needs fixing — once fixed,
`load_text("   # secret\n\t# tab comment\n*.log\n")` must return a list
containing exactly one rule.

## Wildcards

- `*` matches any run of characters except `/`.
- `?` matches a single character except `/`.
- `**` matches any run of characters, including `/`.

A pattern that contains a `/` is matched against the whole relative
path, anchored at both ends: `docs/*.md` excludes `docs/guide.md` but
not `docs/deep/guide.md`. A pattern without a `/` is matched against
each path segment, so `*.log` excludes both `app.log` and
`notes/app.log`, and `build` excludes anything whose path contains a
`build` segment. A trailing `/` on a pattern is ignored.

## Negation

A pattern starting with `!` is a negation. Rules are evaluated top to
bottom and the last matching rule decides: if it is a plain pattern the
path is excluded, if it is a negation the path is re-included. (This is
the behaviour the engine is supposed to have; see `.issue-contract.md`
for the defect that currently breaks it.) When repairing it, spell the
invariant out for future readers as well: the docstring of
`Sieve.decide` must contain, verbatim, the sentence
`The last matching rule wins.` — including the final period.

When several rules match, a negated last match must re-include the path.

A lone `!` with nothing after it is invalid. `compile_pattern("!")`
must raise `PatternError` with the exact message
`negation requires a pattern body`; at the moment it silently builds a
rule that can never match, which is another of the small defects to
clean up. An entirely empty pattern line passed to `compile_pattern`
raises `PatternError` with the message `empty pattern`, as it always
has.

A lone negation must raise `PatternError` with the message `negation requires a pattern body`.

## Case sensitivity

`Sieve` accepts an `ignore_case` keyword argument. Matching is meant to
be case-sensitive by default, so the documented default value of
`ignore_case` is `False`; the constructor currently declares `True` by
mistake and has to be brought back in line with this document. With
`ignore_case=True`, comparisons ignore letter case — for example the
pattern `*.PY` excludes `main.py`.

## Loading rules

`load_text(text)` compiles one rule per pattern line and returns them
as a list. `load_file(path, encoding="utf-8")` reads a file and hands
its contents to `load_text`.
