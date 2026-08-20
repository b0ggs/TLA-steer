# Changelog

FAC04-6: For the 1.2.0 release, this file must gain a new topmost release
section whose heading line begins with `## 1.2.0`, and that section must
contain the exact bullet line `` - Added the `json` subcommand. ``

FAC04-9: Release 1.2.0 bumps the package version:
`python -m tocsmith --version` must print exactly `tocsmith 1.2.0`.

## 1.1.0 - 2026-05-11

- Scanner now skips fenced code blocks.
- Duplicate heading anchors are numbered (`install`, `install-1`, ...).

## 1.0.0 - 2026-03-02

- Initial release with the `generate` subcommand.
