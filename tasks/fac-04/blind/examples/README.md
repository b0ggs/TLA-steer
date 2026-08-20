# Examples

- `sample.md` — the canonical sample document used in docs and tests.
- `sample-toc.md` — exactly what `python -m tocsmith generate examples/sample.md`
  prints (run from the project root).

FAC04-5: For the 1.2.0 release, add `examples/outline.json` to this directory,
containing exactly the JSON document (including the trailing newline) that
`python -m tocsmith json examples/sample.md` prints. The expected content is
shown verbatim in `docs/cli.md` under the `json` subcommand.
