# Examples

The examples/sample directory contains a couple of small files you can point dirlens
at. Try the commands below from the repository root:

```
python -m dirlens scan examples/sample
python -m dirlens ext examples/sample
python -m dirlens newest examples/sample --limit 3
```

When the newest subcommand is implemented, extend the code block above (or add
another fenced code block to this file) so that it also shows, on a line of its own,
the exact invocation `python -m dirlens newest examples/sample --limit 3`.

The CLI must dispatch a `newest` subcommand.
The documentation must show `python -m dirlens newest examples/sample --limit 3`.
