# Examples

This directory holds a sample input and captured outputs so readers can see
what each subcommand produces without running anything.

- `moby.txt` — a short sample paragraph used by all the examples.
- `count-output.txt` — exactly what `python -m wordfreq count examples/moby.txt`
  prints (run from the repository root).

When the `stats` subcommand from `docs/cli.md` is implemented, capture its
output here too: add a file named `stats-output.txt` to this directory holding
exactly what `python -m wordfreq stats examples/moby.txt` prints, which for
this sample is:

```
total_words: 43
unique_words: 38
top_word: and (2)
```
