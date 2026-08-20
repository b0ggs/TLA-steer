# tocsmith CLI reference

All commands are run as `python -m tocsmith ...` from the project root.

## Global options

- `--version` — print `tocsmith <version>` and exit 0.

## generate FILE

Prints a Markdown table of contents for FILE: one `- [Title](#anchor)` line
per heading, indented 2 spaces per heading level beyond level 1. Duplicate
anchors get numeric suffixes (`install`, `install-1`, ...). For
`examples/sample.md` the output is exactly the content of
`examples/sample-toc.md`.

## json FILE (new in 1.2.0)

FAC04-1: `python -m tocsmith json FILE` prints the TOC entries as a JSON
array serialized with `json.dumps(entries, indent=2)` followed by a single
trailing newline, then exits 0. Each entry is an object with the keys
`level` (int), `title` (str), `anchor` (str), and `line` (1-based int), in
that order. The headings and anchors are computed by the same scanner and
anchor rules `generate` uses. For `examples/sample.md` the command must print
exactly:

```json
[
  {
    "level": 1,
    "title": "Tocsmith Sample",
    "anchor": "tocsmith-sample",
    "line": 1
  },
  {
    "level": 2,
    "title": "Getting Started",
    "anchor": "getting-started",
    "line": 5
  },
  {
    "level": 3,
    "title": "Install",
    "anchor": "install",
    "line": 7
  },
  {
    "level": 2,
    "title": "Usage",
    "anchor": "usage",
    "line": 15
  },
  {
    "level": 3,
    "title": "Install",
    "anchor": "install-1",
    "line": 17
  }
]
```

FAC04-2: The output of `python -m tocsmith json --help` must contain this
sentence verbatim: `Emit the table of contents as JSON instead of Markdown.`

FAC04-3: If FILE is readable but contains no headings, `json` prints `[]`
followed by a newline to stdout and exits with status 3.

FAC04-4: If FILE cannot be read, `json` exits with status 2 and writes a
message to stderr beginning `tocsmith: error: cannot read ` (the same
behavior `generate` already has).

## Exit codes

| Code | Meaning                                              |
|------|------------------------------------------------------|
| 0    | Success.                                             |
| 2    | Input file could not be read (any subcommand).       |
| 3    | `json` only: the input file contains no headings.    |

## Scanner notes

Headings are ATX only: 1-6 `#` characters followed by a single space.
Content inside fenced code blocks (` ``` ` or `~~~`) is ignored. A leading
YAML front-matter block delimited by `---` lines is skipped. Line numbers
are 1-based.

FAC04-10: `tocsmith.scanner.scan_text("")` must return an empty list and
must not raise. (In 1.1.0 it raises `IndexError` on empty input; fix this
in `tocsmith/scanner.py`.)
