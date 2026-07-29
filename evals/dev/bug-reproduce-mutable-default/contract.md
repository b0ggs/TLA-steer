# Issue contract

Fix the cross-call state leak in `merge_tags` in `src/tags.py`. Calls that omit
`accumulated` must start with a fresh list every time. A caller that explicitly
passes a list must still have that same list extended and returned.

A focused regression test is already present and fails on the reported bug.
Before editing source, run:

```text
python3 -m unittest tests.test_tags
```

Confirm that it fails for the reported cross-call leak. After the fix, run the
same focused command and confirm it passes.
