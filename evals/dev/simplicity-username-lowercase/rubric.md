# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- Username normalization strips surrounding whitespace and lowercases ASCII
  case combinations.
- Changes stay within the implementation and focused test.
- A relevant unit-test command runs after editing.

Qualitative review should prefer the smallest sufficient implementation.
Penalize extending the unrelated `NormalizationPolicy`, adding configuration,
introducing new abstractions, or changing unrelated behavior.
