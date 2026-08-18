# Handoff digest

Use `PYTHONPATH=src python3 -m handoff_digest show` to render one JSON record.

## Existing compatibility

G1 — The existing `show` command remains compatible: `PYTHONPATH=src python3 -m handoff_digest show '{"title":"Ready","owner":"Ada"}' --tag OPS` prints exactly `* OPS: Ready (Ada)` followed by one newline and exits 0.

## Pending command boundary

R5 — Add `publish INPUT OUTPUT [--tag TAG]` to the module CLI. An explicit `--tag` overrides the configured default; success writes the digest, prints the `OUTPUT` argument followed by one newline, and exits 0.

## Pending user documentation

R7 — Add a `## Publish a digest` README section containing `PYTHONPATH=src python3 -m handoff_digest publish records.jsonl digest.md --tag OPS` and the sentence `Blank JSONL lines are ignored.`
