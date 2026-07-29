# Issue contract

Fix the real executable so this command succeeds:

```text
bin/sample-export --format json
```

It must exit `0`, write no stderr, and print exactly this JSON value followed by
a newline:

```json
{"count": 2, "items": ["alpha", "beta"]}
```

The package function and its unit tests already pass. The executable currently
calls a stale function name. Preserve the existing executable interface and
text mode. Add a focused test if useful, and after editing run both the unit
tests and the real command above.
