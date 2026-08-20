# Normalization pipeline

`addrbook.pipeline.run` applies two stages:

1. **Normalize** each record with `addrbook.normalize.normalize_record`:
   - `name` is cleaned with `clean_name`,
   - `email` is cleaned with `normalize_email`,
   - every entry in the `phones` list is cleaned with
     `addrbook.phones.normalize_phone`.
2. **Deduplicate** with `addrbook.dedupe.dedupe`, keeping the first record
   for each key value (default key: `email`). With `strict=True`, a repeated
   key value raises `addrbook.errors.DuplicateKeyError` instead.

Phone inputs whose digits do not form a NANP number are reduced to their
digits only.

## Acceptance notes (1.4.0)

- FAC10-3: `normalize_record` must return a new dict (not the same object it
  was given) and must not mutate its input: after the call, the input dict
  must compare equal to a snapshot taken before the call, and appending an
  element to the returned record's `"phones"` list must not change the input
  record's `"phones"` list. A shallow copy of the top-level dict plus a newly
  built `"phones"` list is sufficient; deep copies of other nested values are
  not required.
- FAC10-6: `addrbook.config.DEFAULTS["phone_style"]` must equal
  `"nanp-dashed"`.
- FAC10-7: the docstring of `normalize_phone` must contain this exact
  sentence: `Returns NANP numbers in +1-XXX-XXX-XXXX form.`
- FAC10-8: with `strict=True`, `dedupe` must raise `DuplicateKeyError` whose
  message is exactly `duplicate contact key: ` followed by the repeated key
  value. Example: if the repeated email is `ada@example.com`, then
  `str(exc)` must be exactly `duplicate contact key: ada@example.com`.
