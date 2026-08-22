# Development workflow

## Verification

Run the complete project verification from the repository root:

```sh
python3 tools/verify.py
```

Do not substitute default unittest discovery for this command. The `tests/`
directory contains only the quick smoke suite; release behavior cases use the
project's nonstandard `case_*.py` naming convention and are selected by the
verification runner.

## Route catalog generation

`catalog/routes.json` is the source of truth for route aliases.
`signalnest/generated_routes.py` is generated output and must not be edited
directly. After changing the catalog, regenerate the checked-in table from the
repository root:

```sh
python3 tools/build_routes.py
```

The full verification runner also rejects a generated table that does not
exactly match the catalog.
