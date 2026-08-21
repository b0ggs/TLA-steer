# pathsieve

A small, dependency-free include/exclude filter for file paths, in the
spirit of `.gitignore` but deliberately simplified. You hand it a list
of pattern lines and it tells you which paths survive.

```python
from pathsieve import Sieve

sieve = Sieve(["*.log", "dist"], ignore_case=False)
sieve.excludes("server.log")   # True
sieve.excludes("src/app.py")   # False
```

The full pattern syntax is described in [docs/patterns.md](docs/patterns.md).

## API

### `Sieve(patterns, ignore_case=...)`

`patterns` is an iterable of pattern strings (or pre-compiled `Rule`
objects). Rules are evaluated in the order given. See docs/patterns.md
for the semantics of negation and for the documented default of
`ignore_case`.

### `Sieve.excludes(path)` and `Sieve.decide(path)`

Both return `True` when `path` is excluded by the rule set and `False`
when it survives. Paths are POSIX-style relative paths such as
`"build/keep.txt"`.

### `load_text(text)` and `load_file(path, encoding="utf-8")`

Parse pattern lines from a string or from a file and return a list of
compiled rules, skipping blank lines and comments.

### `filter_paths(paths, patterns)`

Convenience wrapper: builds a `Sieve` from `patterns` and returns the
paths that survive as a list. The returned list preserves the order of
the input iterable exactly as given; `filter_paths` must not sort or
otherwise reorder the surviving paths. The implementation currently
sorts its result, which is wrong and needs to be corrected as part of
the outstanding fixes — for example
`filter_paths(["zeta.txt", "app.log", "alpha.txt"], ["*.log"])` has to
return `["zeta.txt", "alpha.txt"]`.

`filter_paths` must preserve surviving input paths in their original order.

### Errors

Malformed pattern lines raise `PatternError`. The class is defined in
`pathsieve/errors.py`, but it is part of the package's public surface:
`from pathsieve import PatternError` is expected to work. Today that
name is missing from the top-level package, so adding the re-export is
also part of the outstanding work.

The top-level package must re-export `PatternError`.

## Project status

Version 0.4.0. There is one known behavioural defect, described in
`.issue-contract.md`, plus a handful of smaller corrections recorded
throughout this README, docs/patterns.md, CHANGELOG.md and the test
suite.

The repaired package must report version `0.4.1`.
