# durafmt

`durafmt` parses compact duration strings such as `"1h30m"` into whole
seconds and formats second counts back into readable strings. Pure Python,
standard library only.

## Usage

```
>>> import durafmt
>>> durafmt.parse("90m")
4500
>>> durafmt.parse("1h")
3600
>>> durafmt.format_duration(3661)
'1h 1m 1s'
```

Supported units: `d` (days), `h` (hours), `m` (minutes), `s` (seconds).

> Acceptance note TRIAL-A-8 (full wording in docs/upgrading.md): the usage
> example above shows the pre-fix parser output for `"90m"` and must be
> updated as part of release 1.2.1.

## Release notes

See CHANGELOG.md, and docs/upgrading.md for the 1.2.1 acceptance notes
(TRIAL-A-2 through TRIAL-A-10).
