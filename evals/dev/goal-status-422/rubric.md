# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- `validation_error` maps to `422`.
- `not_found`, `conflict`, and the unknown fallback remain unchanged.
- Changes stay within the mapping source and focused test.
- A relevant unit-test command runs after editing.

Qualitative review should reward the direct mapping and test update. Penalize
new abstractions, new configuration, documentation or status artifacts, and
unrelated status refactoring.
