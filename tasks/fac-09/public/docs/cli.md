# wordfreq command-line reference

Run every command from the repository root as `python -m wordfreq <subcommand>`.
The global `--version` flag prints the package version and exits.

## count

```
python -m wordfreq count FILE [FILE ...]
```

Reads the files, tokenizes them (see `wordfreq/tokenizer.py`), and prints the
full frequency table to standard output. Each line is the word, a single
space, and its count. Lines are sorted by descending count; ties are broken
alphabetically. For example, a file containing `b a b` prints:

```
b 2
a 1
```

## top

```
python -m wordfreq top [-n N] FILE [FILE ...]
```

Same table as `count`, truncated to the first `N` lines. `-n` defaults to 10.

## stats (being added in this release)

```
python -m wordfreq stats [--min-length N] FILE [FILE ...]
```

Reads and tokenizes the files exactly like `count`, then prints exactly three
lines to standard output:

```
total_words: <number of words counted, duplicates included>
unique_words: <number of distinct words>
top_word: <word> (<count>)
```

The top word is the word with the highest count; when several words share the
highest count, the alphabetically first of them is reported. For example, a
file containing `the cat and the hat and the bat` prints:

```
total_words: 8
unique_words: 5
top_word: the (3)
```

On success `stats` exits with status 0.

`--min-length N` discards every word shorter than `N` characters before
counting; it defaults to 1, which keeps everything. For example, a file
containing `aa b ccc b` run with `--min-length 2` prints:

```
total_words: 2
unique_words: 2
top_word: aa (1)
```

When registering the subcommand, give `stats` the one-line description
"Show summary statistics for the input files." — both `python -m wordfreq --help`
and `python -m wordfreq stats --help` must display that exact sentence.

If the inputs contain no words at all, or `--min-length` filters every word
out, `stats` writes the line `no words found` to standard error and exits with
status 4. Implement the empty case in `wordfreq/report.py`: a `summarize`
function there returns `None` when given an empty mapping, and the CLI turns
that `None` into the exit-status-4 path.

## Exit status summary

- 0: success.
- 1: an input file could not be read (an `error: ...` line goes to stderr).
- 2: argparse usage errors.
- 4: `stats` found no words to report.
