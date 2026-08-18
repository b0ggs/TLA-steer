# Header tools

This small module reads string-valued headers and formats them for reports.

PUBLIC-R3: When a header is absent, `get_header` must return the caller-supplied `default` value.

PUBLIC-R4: Set `missing_header` in `config/defaults.json` to the exact string `<missing>`.
