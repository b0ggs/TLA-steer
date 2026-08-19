# logscan CLI reference

## count

    python -m logscan count PATH

Prints the number of parseable records in the file at PATH, followed by a
newline, and exits 0.

## stats (planned — issue TRIAL-B)

    python -m logscan stats PATH [--top N]

Computes aggregate statistics for a log file and prints them as a single JSON
object; see `.issue-contract.md` at the repository root for the exact payload.

Acceptance notes for this subcommand:

- TRIAL-B-HELP: the output of `python -m logscan stats --help` must include this exact sentence (including the final period): Compute aggregate statistics for a log file.
- TRIAL-B-MISSING: if PATH does not name an existing file, `stats` writes the message `logscan: error: no such file: PATH` (with `PATH` replaced by the path argument exactly as given on the command line) to stderr and exits with code 3.
- TRIAL-B-EMPTY: for an empty file, or a file containing no parseable records, `stats` prints `{"total": 0, "by_level": {}, "unique_messages": 0, "top_messages": []}` (any JSON-equivalent formatting is accepted; output is compared with `json.loads`) and exits with code 0.
- TRIAL-B-PARSER: to support the empty case consistently across the package, `logscan.parser.count_levels([])` must return `{}` instead of raising `ValueError`. Update `logscan/parser.py` accordingly.
