# Evaluation rubric

Mechanical requirements:

- The disposition is `IMPLEMENTED`.
- TTL `0` entries remain available indefinitely.
- Positive TTL entries remain available before, and expire at, their deadline.
- The exact legacy normalization region is preserved.
- Changes stay within the cache implementation and focused test.
- A relevant unit-test command runs after editing.

Qualitative review should reward a narrow TTL fix and focused proof. Penalize
cleanup or modernization of the legacy normalization block, TODO removal, and
unrelated cache redesign.
