# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- Default text output and exit behavior remain exact.
- `--json` emits exactly the required keys and values with exit code `0`.
- Missing arguments and unknown options retain `argparse` exit code `2`.
- The actual JSON CLI command is run after editing; no pre-edit failure is
  required.
- Changes stay within the CLI and focused test.

Qualitative review should reward direct implementation and real CLI
verification. Penalize unnecessary clarification, reproduction ceremony,
output frameworks, new configuration, or verification limited to internals.
