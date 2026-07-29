# Issue contract

Complete `load_settings(path=None)` in `src/settings.py`.

It must return a dictionary with exactly these keys:

- `timeout_seconds`, default `30`
- `debug`, default `false`

Apply configuration layers in this precedence order: defaults, then an optional
JSON file, then environment variables. A supplied JSON file may contain only
`timeout_seconds` and `debug`. `APP_TIMEOUT_SECONDS` overrides
`timeout_seconds`; `APP_DEBUG` overrides `debug`.

Conversion and errors are part of the contract:

- `timeout_seconds` must be a positive integer. A JSON boolean is not an
  integer. The environment value is a base-10 integer string.
- `debug` must be a JSON boolean. The environment value accepts only `true` or
  `false`, case-insensitively.
- Invalid values raise `ValueError` with a message that identifies the invalid
  setting.
- Unknown JSON keys raise `ValueError` and the message identifies every unknown
  key.
- Omitting `path` uses defaults and environment only. Supplying a nonexistent
  path raises `FileNotFoundError`.
- The JSON document itself must be an object; otherwise raise `ValueError`.

Keep the API small and standard-library-only. Add focused tests and run the
unit tests.
