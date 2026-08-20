# dirlens command reference

Every command is invoked as `python -m dirlens <command> ...` from the repository
root. All file paths printed by dirlens are relative to the scanned directory and use
forward slashes.

## Global options

`python -m dirlens --version` prints the program name and version, separated by a
single space, for example `dirlens 0.2.0`, and exits with status 0.

## scan

`python -m dirlens scan PATH`

Walks PATH recursively and prints one line per regular file: the file's relative
path, a single tab character, and the file's size in bytes. Lines are sorted by
relative path in ascending string order. The command exits with status 0 on success.
If PATH does not exist, scan prints an error message to standard error and exits with
status 3.

## ext

`python -m dirlens ext PATH`

Walks PATH recursively and prints one line per extension: the extension label, a
single tab character, and the number of files carrying that extension. The extension
label is the text after the final dot of the file name, without the dot; files whose
names contain no extension are counted under the label `(none)`. Lines are sorted by
label in ascending string order. Like scan, ext exits with status 0 on success and
prints an error to standard error and exits with status 3 when PATH does not exist.

## newest (to be implemented)

`python -m dirlens newest PATH [--limit N] [--json]`

The newest command walks PATH recursively and reports the most recently modified
regular files. In the plain text mode each output line consists of the file's
modification time, a single tab character, and the file's path relative to PATH
written with forward slashes. The modification time is converted to UTC, truncated to
whole seconds, and formatted as `YYYY-MM-DDTHH:MM:SSZ`. Entries appear newest first,
and two files sharing a modification time are ordered by relative path in ascending
string order. The `--limit N` option prints at most N entries; the default used when
the option is absent is stated in the README. Passing `--json` switches the command
to print a JSON array on standard output instead of text lines, honouring the same
ordering and the same limit, where every element is an object with exactly two keys,
`path` and `mtime`, holding the relative path and the timestamp string described
above. When PATH exists but contains no files at all, newest prints nothing to
standard output and exits with status 0, and in JSON mode it prints an empty array.
Like the other commands, newest must print an error message to standard error and
exit with status 3 when PATH does not exist. Finally, the help text printed by
`python -m dirlens newest --help` has to contain, exactly as written here, the
sentence "List the most recently modified files in a directory tree."

## Exit codes

- 0 — success.
- 2 — command line usage error (reported by argparse).
- 3 — the given PATH does not exist.
