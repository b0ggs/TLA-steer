# Changelog

Acceptance note (FAC02-2): the `## 1.2.1` section below must contain, between
the `## 1.2.1` heading and the next `## ` heading, the exact line:

- Fixed: override layers now take precedence over base layers.

Acceptance note (FAC02-3): for this release `inimerge.__version__` (defined in
`inimerge/__init__.py`) must equal `1.2.1`.

## 1.2.1 - 2026-08-19

- Fixed: override layers now take precedence over base layers.
- Fixed: `parse` keeps `key =` entries as empty strings.
- Fixed: `ParseError` messages now follow the documented wording.
- Fixed: the CLI exits with status 2 when an input file fails to parse.
- Changed: `dumps` writes `key = value` entries with sorted keys.

## 1.2.0 - 2026-07-30

- Added `merge_all` for folding any number of layers.
- Added the `inimerge.cli` command line front end.

## 1.1.0 - 2026-05-12

- Added the `dumps` writer.

## 1.0.0 - 2026-03-02

- Initial release: `parse` and `merge`.
