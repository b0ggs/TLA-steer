# Changelog

## Unreleased

FAC01-3: The 0.4.1 release must add, above the 0.4.0 section, a section
headed exactly `## 0.4.1` that contains this bullet line exactly:
`- Fixed: median now averages the two middle values for even-sized columns`

## 0.4.1

- Fixed: median now averages the two middle values for even-sized columns
- Fixed: unknown-column errors now use the documented wording and exit status 2
- Changed: DEFAULT_PRECISION is now 4
- Changed: load_rows raises ValueError for input with no data rows

## 0.4.0

- Added JSON summary output with configurable precision
- Added --version flag

## 0.3.0

- Initial public release of the stats command
