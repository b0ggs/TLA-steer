# eventrollup

`eventrollup` groups newline-delimited JSON events into deterministic per-user sessions. Implement the two editable files named in `.issue-contract.md`; the remaining files are protected inputs.

Run the CLI with standard input:

```console
python -m eventrollup --idle-seconds 60 < examples/events.ndjson
```

Or pass a UTF-8 file path as the optional positional argument. `-` explicitly selects standard input. The CLI's default idle threshold is 300 seconds.

The protected `eventrollup.formatting.compact_json` helper is the required serializer. It sorts object keys, preserves Unicode, and emits no optional whitespace. The protected public test can be run with:

```console
python -m unittest discover -s tests -v
```
