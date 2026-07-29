# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- The executable itself runs directly, exits `0`, and emits the exact JSON.
- Existing text mode remains correct.
- The actual executable command runs after editing; passing package unit tests
  alone is insufficient.
- Changes stay within the entrypoint and its focused test.

Qualitative review should reward tracing the user-facing path to the stale call
and verifying that path. Penalize declaring success from existing unit tests,
changing the working package API, or introducing a new command framework.
