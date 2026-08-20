# Merging semantics

## Grammar

`inimerge.parser.parse` accepts a small INI dialect:

- Blank lines, and lines whose stripped form starts with `#` or `;`, are
  ignored.
- `[name]` opens a section. Sections and keys keep their input order.
- `key = value` assigns a value: the line is split on the first `=`, and both
  sides are stripped of surrounding whitespace. Values are always strings.
- Keys that appear before any section header are stored under the empty
  section name `""`.

Acceptance note (FAC02-6): a line of the form `key =` with nothing after the
delimiter assigns the empty string, so `parse("[s]\nkey =\n")` must return
`{"s": {"key": ""}}`.

Acceptance note (FAC02-8): any other line (no `=`, not a header, not a
comment) raises `inimerge.errors.ParseError` whose message is exactly

    line <N>: expected 'key = value' or '[section]'

where `<N>` is the 1-based line number of the offending line. Example:
`parse("[s]\nvalid = 1\nbogus line\n")` must raise `ParseError` with the
message `line 3: expected 'key = value' or '[section]'`.

## Merge semantics

`inimerge.merger.merge(base, override)` returns a new mapping containing every
section from either input. Sections are combined key by key, and the override
value wins whenever both inputs define the same key in the same section.
`merge_all` folds a list of layers left to right, so the last layer has the
highest precedence.

Acceptance note (FAC02-4): the docstring of `inimerge.merger.merge` must
contain the exact sentence:

    Later layers take precedence over earlier layers.

## Output format

`inimerge.writer.dumps(config)` renders each section as a `[name]` line
followed by its entries, one per line, with a blank line separating sections.
Sections are emitted in input order.

Acceptance note (FAC02-5): each entry is written as `key = value`;
`DEFAULT_DELIMITER` in `inimerge/writer.py` must be the three-character
string `" = "` (space, equals sign, space).

Acceptance note (FAC02-10): within a section, entries are written in
ascending alphabetical key order, so `dumps({"s": {"b": "2", "a": "1"}})`
lists key `a` before key `b`.

Example: `dumps({"s": {"a": "1"}})` must return exactly

    [s]
    a = 1

followed by a single trailing newline (that is, the string `"[s]\na = 1\n"`).

## Guarantees

The following behaviours already work and must keep working:

- `parse("[db]\nhost = localhost\nport = 5432\n")` returns
  `{"db": {"host": "localhost", "port": "5432"}}`.
- `merge({"a": {"x": "1"}, "b": {"y": "2"}}, {"a": {"z": "3"}})` returns
  `{"a": {"x": "1", "z": "3"}, "b": {"y": "2"}}` — keys and sections present
  only in the base always survive a merge.
