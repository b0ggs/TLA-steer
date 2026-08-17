# Bookmarks fixture

This standard-library-only project keeps a small JSON bookmark collection.
Run its existing tests from this directory with:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Archive command

**M2-A-009 — Documentation update.** Document the completed archive command
here, including one runnable example that uses an input JSON file, a label, and
an output JSON file.  State that it preserves input ordering and that the
input file is not modified.

Bookmark JSON is a JSON array.  Each element is an object with `title`, `url`,
and `labels` fields; `archived` is optional in old files.
