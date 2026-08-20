# Example transcripts

Recorded shell sessions that show the tool in use:

- `rotate-session.txt` — a `rotate` followed by a `list`.
- `prune-session.txt` — a dry run followed by a real `prune`.

> **FAC05-8 (acceptance note).** Add a new transcript file
> `examples/prune-session.txt` whose content is exactly the eight lines
> shown inside the fenced block below, in that order (a trailing
> newline at the end of the file is fine):
>
> ```
> $ python -m logrotor prune --dry-run --keep 2 logs/
> would prune: app.log.20260301090000
> would prune: app.log.20260302090000
> $ python -m logrotor prune --keep 2 logs/
> pruned: app.log.20260301090000
> pruned: app.log.20260302090000
> $ python -m logrotor prune --keep 2 logs/
> nothing to prune
> ```
