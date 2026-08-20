# dirlens

dirlens is a small, dependency-free inventory tool for directory trees. Point it at a
folder and it lists every file with its size, or summarises how many files exist per
extension. All commands run through the package entry point, for example
`python -m dirlens scan .`.

## Commands

- `scan PATH` — list every file under PATH together with its size in bytes.
- `ext PATH` — count files per extension.
- `newest PATH` — planned for the next release; the full specification lives in
  docs/cli.md.

Run `python -m dirlens --version` to see the installed version.

## Defaults and conventions

Paths in all output are relative to the scanned directory and always use forward
slashes, regardless of platform. scan and ext walk the entire tree; there is no depth
option. The newest command prints five entries when no --limit option is passed on
the command line. Shipping newest is a feature release, so once the command works
`python -m dirlens --version` must report `dirlens 0.3.0`.

## Testing

The test suite uses only the standard library's unittest module. Existing tests live
in tests/ and run with `python -m unittest discover -s tests -t .` from the
repository root. The newest command has to arrive with its own module,
tests/test_newest.py, which must pass with at least one test when invoked as
`python -m unittest tests.test_newest` from the repository root.

## Layout

- `dirlens/` — the package: CLI wiring in cli.py, filesystem walking in scanner.py,
  report building in report.py.
- `docs/cli.md` — the command reference.
- `examples/` — a small sample tree and ready-to-run commands.
