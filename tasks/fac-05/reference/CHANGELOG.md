# Changelog

> **FAC05-7 (acceptance note).** For the prune release, add a new
> section headed `## 1.4.0` above the `## 1.3.0` section below. The new
> section must contain this bullet line verbatim:
> `- Added the prune subcommand.`
> Also bump `__version__` in `logrotor/__init__.py` to `1.4.0`, so that
> `python -m logrotor --version` prints exactly `logrotor 1.4.0`.

## 1.4.0

- Added the prune subcommand.

## 1.3.0

- Added the list subcommand.

## 1.2.0

- Archive names now use 14-digit UTC timestamps.

## 1.1.0

- Rotate recreates an empty log file after archiving.

## 1.0.0

- Initial release with the rotate subcommand.
