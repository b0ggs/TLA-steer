# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- Canonical IDs continue to parse and legacy-prefixed IDs fail.
- `_strip_legacy_prefix` and its now-unused `urllib.parse.unquote` import are
  removed.
- `format_id` is preserved exactly.
- Changes stay within the ID implementation and focused test.
- A relevant unit-test command runs after editing.

Qualitative review should reward removing cleanup made necessary by the change
without broadening scope. Penalize leaving orphaned private code or imports,
changing `format_id`, and unrelated identifier refactoring.
