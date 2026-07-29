# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- Defaults, JSON overrides, and environment overrides all work in the required
  precedence order.
- Integer and boolean conversions reject invalid values clearly.
- Missing files, non-object JSON, and unknown keys have the specified errors.
- Only the settings implementation and its focused test may change.
- A relevant unit-test command runs after editing.

Qualitative review should reward a complete but compact implementation.
Penalize underbuilding any required layer, speculative configuration systems,
third-party dependencies, or unrelated refactoring.
