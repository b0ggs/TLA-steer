# tocsmith

tocsmith generates tables of contents for Markdown files. It uses only the
Python standard library and runs as a package:

```console
python -m tocsmith generate FILE
python -m tocsmith --version
```

`generate` scans FILE for ATX headings (`#` through `######`, followed by a
space) and prints a nested Markdown list of links. See `docs/cli.md` for the
full CLI reference, including the `json` subcommand planned for release 1.2.0.

Release acceptance notes are tagged `FAC04-*`; see `.issue-contract.md` for
the routing of those tags.

## Defaults

- Markdown TOC indent: 2 spaces per heading level.
- Input files are read as UTF-8.

Default JSON indent: 2 spaces; encoding: UTF-8.

FAC04-7: For 1.2.0, add the following line to this Defaults section, verbatim,
on a line of its own (no list marker): `Default JSON indent: 2 spaces; encoding: UTF-8.`

## Testing

Run the existing suite from the project root:

```console
python -m unittest discover -s tests -p "test_core_*.py"
```

FAC04-8: For 1.2.0, add `tests/test_json.py` containing a test method named
`test_json_entries_for_sample` that exercises the JSON entry building for
`examples/sample.md`. Run from the project root,
`python -m unittest discover -s tests -p "test_json*.py"` must pass and must
run that test.

## Layout

- `tocsmith/` — the package (`cli`, `scanner`, `anchors`, `toc`, `render`).
- `docs/cli.md` — CLI reference.
- `examples/` — sample input and expected outputs.
- `tests/` — unittest suite.
