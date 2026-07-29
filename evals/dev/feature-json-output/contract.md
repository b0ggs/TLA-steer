# Issue contract

Add a `--json` flag to `sample_cli.py`.

The command continues to require one positional `name`.

- `python3 sample_cli.py Ada` prints exactly `Hello, Ada!` followed by a
  newline and exits `0`.
- `python3 sample_cli.py --json Ada` prints one JSON object followed by a
  newline and exits `0`. The object has exactly these keys and values:
  `{"greeting": "Hello, Ada!", "name": "Ada"}`.
- A missing name or an unknown option keeps normal `argparse` behavior: usage
  goes to stderr and the process exits `2`.

There is no supplied failing regression test to reproduce. Implement the clear
feature, add focused tests, run the unit tests, and after editing exercise the
actual JSON CLI path with:

```text
python3 sample_cli.py --json Ada
```
