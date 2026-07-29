# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- Default invocations do not share state in any call order.
- Explicit accumulator lists are still extended in place and returned.
- The supplied focused test is run and observed failing before the first source
  edit, then run and observed passing after the edit.
- Changes stay within the tag implementation and focused test.

Qualitative review should reward direct reproduction and proof of the same
behavior after a small fix. Penalize editing before reproducing, relying only
on unrelated tests, or redesigning the tag API.
