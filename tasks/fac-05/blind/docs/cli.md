# logrotor CLI reference

`logrotor` is invoked as `python -m logrotor`.

## Global options

- `--version` — print `logrotor`, a space, and the version number (for
  example `logrotor <version>`), then exit with status 0.

## Exit codes

| Code | Meaning |
| ---- | ------- |
| 0 | Success. |
| 2 | Usage error (bad flags or arguments; reported by argparse). |
| 3 | The directory named on the command line does not exist. Before exiting, the tool prints `error: no such directory: <directory>` to standard error. |

## Archive naming

`rotate` renames each `NAME.log` file to `NAME.log.<TS>`, where `<TS>` is
a 14-digit UTC timestamp (`YYYYMMDDHHMMSS`), then recreates `NAME.log`
empty. A file is an *archive* exactly when its name has that
`NAME.log.<TS>` shape. Because the timestamp is zero-padded and
fixed-width, sorting archive filenames in ascending text order also
sorts them oldest to newest; the archive with the largest timestamp is
the newest.

## Subcommands

### `rotate DIRECTORY`

Rotates every `*.log` file in `DIRECTORY`. For each rotated file it
prints one line, `rotated: NAME.log -> NAME.log.<TS>`, and exits with
status 0.

### `list DIRECTORY`

Prints the archive filenames found in `DIRECTORY`, one per line, in
ascending filename order, and exits with status 0.

## Planned subcommand: `prune` (acceptance notes)

> **FAC05-1 (acceptance note).** Add a `prune` subcommand:
>
> ```
> python -m logrotor prune [--keep N] [--dry-run] DIRECTORY
> ```
>
> For each log base name, `prune` keeps the `N` newest archives (the
> largest timestamps) and deletes every older archive of that base name.
> Archives of different base names are counted separately. Live `*.log`
> files and non-archive files are never touched. On success `prune`
> exits with status 0 and its standard output is exactly one line per
> deleted file, in ascending filename order, and nothing else. Each line
> has the form:
>
> ```
> pruned: <filename>
> ```

> **FAC05-2 (acceptance note).** The output of
> `python -m logrotor prune --help` must contain this sentence verbatim:
> `Remove old rotated archives, keeping the newest N per log.`

> **FAC05-3 (acceptance note).** `prune` follows the exit-code table
> above: when `DIRECTORY` does not exist, it prints
> `error: no such directory: <directory>` to standard error and exits
> with status 3.

> **FAC05-4 (acceptance note).** With `--dry-run`, `prune` deletes
> nothing, exits with status 0, and its standard output is exactly one
> line per archive that would have been deleted, in ascending filename
> order, and nothing else. Each line has the form:
> `would prune: <filename>`.

> **FAC05-5 (acceptance note).** When no archive qualifies for deletion
> — including when `DIRECTORY` contains no archives at all — `prune`
> prints exactly `nothing to prune` on standard output and exits with
> status 0. Handle the empty-directory boundary in `logrotor/scan.py`:
> add a function `find_archives(directory)` there that returns the
> archive filenames of `directory` in ascending order, and returns an
> empty list (`[]`) for a directory containing no archives.
