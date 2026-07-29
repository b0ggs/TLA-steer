# Issue contract

Remove support for legacy-prefixed IDs from `parse_id` in `src/ids.py`.
`parse_id` must accept only the same canonical `kind:number` strings already
accepted by `parse_canonical_id`.

Remove the private legacy helper and the import used only by that helper once
they become orphaned. Preserve the unrelated `format_id` function exactly.
Update focused tests and run the unit tests.
