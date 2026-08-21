"""A tiny in-memory notes collection."""

import json


class Notes:
    """Store notes for the lifetime of this object."""

    def __init__(self):
        self._notes = []
        self._next_id = 1

    def add(self, title, body="", tags=()):
        """Add a note and return its integer id."""
        if not isinstance(title, str) or not title.strip():
            raise ValueError("title must be a non-empty string")
        if not isinstance(body, str):
            raise TypeError("body must be a string")

        stored_tags = list(tags)
        if not all(isinstance(tag, str) for tag in stored_tags):
            raise TypeError("tags must contain only strings")

        note = {
            "id": self._next_id,
            "title": title,
            "body": body,
            "tags": stored_tags,
        }
        self._notes.append(note)
        self._next_id += 1
        return note["id"]

    def get(self, note_id):
        """Return a detached copy of a note, or raise KeyError."""
        for note in self._notes:
            if note["id"] == note_id:
                return self._copy_note(note)
        raise KeyError(note_id)

    def all(self):
        """Return detached copies in insertion order."""
        return [self._copy_note(note) for note in self._notes]

    def search(self, query=None, tags=None):
        """Return detached notes matching the query and all requested tags."""
        if query is not None and not isinstance(query, str):
            raise TypeError("query must be a string or None")

        folded_query = query.casefold() if query else None
        requested_tags = self._normalize_tags(tags)

        matches = []
        for note in sorted(self._notes, key=lambda item: item["id"]):
            if folded_query is not None and not (
                folded_query in note["title"].casefold()
                or folded_query in note["body"].casefold()
            ):
                continue

            note_tags = {tag.strip().casefold() for tag in note["tags"]}
            if not requested_tags.issubset(note_tags):
                continue

            matches.append(self._copy_note(note))

        return matches

    def export_json(self):
        """Return the collection in the deterministic JSON export format."""
        notes = []
        for note in sorted(self._notes, key=lambda item: item["id"]):
            exported_note = self._copy_note(note)
            exported_note["tags"].sort()
            notes.append(exported_note)

        document = {"schema_version": 1, "notes": notes}
        return json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"

    @staticmethod
    def _normalize_tags(tags):
        if tags is None:
            return set()

        normalized = set()
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError("tags must contain only strings")
            normalized.add(tag.strip().casefold())
        return normalized

    @staticmethod
    def _copy_note(note):
        return {
            "id": note["id"],
            "title": note["title"],
            "body": note["body"],
            "tags": list(note["tags"]),
        }
