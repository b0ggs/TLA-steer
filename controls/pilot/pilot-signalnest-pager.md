# SignalNest maintainer instructions

Run commands from the repository root. SignalNest is a small Python project
that uses only the standard library; do not introduce third-party runtime or
test dependencies unless the project specification is deliberately changed.

## Repository map and sources of truth

- `catalog/routes.json` is the authoritative mapping from user-facing route
  aliases to canonical route names.
- `signalnest/generated_routes.py` is a checked-in generated artifact. It is
  consumed by `signalnest/router.py`, but it is never the place to make route
  changes.
- `signalnest/router.py` owns input handling and route-resolution behavior.
- `signalnest/__init__.py` defines the package's public API. Keep intended
  public names imported there and listed in `__all__`.
- `tests/test_*.py` contains the quick smoke suite.
- `checks/case_*.py` contains release behavior cases. This nonstandard naming
  is intentional: default unittest discovery does not run these cases.
- `tools/verify.py` is the authoritative complete verification entry point.

## Generated route table workflow

To add, remove, or change an alias, edit `catalog/routes.json`, then regenerate
the checked-in Python table:

```sh
python3 tools/build_routes.py
```

Commit the catalog and regenerated `signalnest/generated_routes.py` together.
Do not hand-edit the generated module. The generator validates that the
catalog is a nonempty JSON object whose keys and values are strings, sorts
aliases for deterministic output, and writes the complete table. The full
verification command compares that output byte-for-byte with a fresh render
and fails with `generated route table is stale` when they differ.

## Verification commands

For a fast smoke check, run:

```sh
python3 -m unittest
```

Before handing off any change, run the complete project verification:

```sh
python3 tools/verify.py
```

Do not substitute default unittest discovery for the complete command.
`tools/verify.py` first checks generated-file freshness and then discovers the
release suite under `checks/` with the `case_*.py` pattern.

## Coding and test conventions

- Keep implementation, tools, and tests compatible with the Python standard
  library.
- Preserve the public behavior exposed by `signalnest`: `resolve_route`
  accepts strings, resolves aliases without regard to letter case, and raises
  `UnknownRoute` for unregistered aliases; non-string values raise
  `TypeError`. Release cases also define normalization requirements such as
  ignoring surrounding whitespace.
- Add ordinary smoke coverage in `tests/test_*.py` using `unittest`. Add
  release behavior coverage in `checks/case_*.py` so the complete verifier
  selects it.
- Keep generated-file checks and release-case discovery centralized in
  `tools/verify.py`; preserve the deliberate distinction between the smoke
  and release suites.
- Make route data changes in the catalog and resolver-semantics changes in
  `signalnest/router.py`. Avoid duplicating catalog entries or hand-maintained
  route tables elsewhere.
