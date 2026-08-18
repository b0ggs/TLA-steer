"""Digest-line rendering.

R3 — Missing-owner boundary

`render_record(record, tag)` must render a record without an `owner` key by using the literal owner text `unassigned`; records that contain `owner` keep that value.
"""


def render_record(record, tag):
    return f"* {tag}: {record['title']} ({record['owner']})"
