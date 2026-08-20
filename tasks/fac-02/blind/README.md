# inimerge

`inimerge` merges layered INI-style configuration files: a base file plus any
number of override files, folded left to right into a single configuration.

Pure standard library; no third-party dependencies.

## Library use

```python
import inimerge

with open("examples/base.ini", encoding="utf-8") as fh:
    base = inimerge.parse(fh.read())
with open("examples/override.ini", encoding="utf-8") as fh:
    override = inimerge.parse(fh.read())

print(inimerge.dumps(inimerge.merge(base, override)))
```

## Command line

```
python -m inimerge.cli examples/base.ini examples/override.ini
```

The merged configuration is printed to stdout. Exit status 0 means success.

Acceptance note (FAC02-9): when any input file fails to parse, `main` in
`inimerge/cli.py` must return exit status 2. (Usage errors already use
status 2; unreadable files keep using status 1.)

## Documentation

- `docs/merging.md` — grammar, merge semantics, output format, guarantees.
- `CHANGELOG.md` — release history.

## Tests

```
python -m unittest discover -s tests
```
