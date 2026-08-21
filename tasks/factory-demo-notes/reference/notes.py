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

    def search(self, query="", tags=None):
        folded_query = query.casefold()
        wanted = {
            tag.strip().casefold()
            for tag in (() if tags is None else tags)
        }
        matches = []
        for note in self._notes:
            haystack = (note["title"].casefold(), note["body"].casefold())
            note_tags = {tag.strip().casefold() for tag in note["tags"]}
            if any(folded_query in text for text in haystack) and wanted.issubset(note_tags):
                matches.append(self._copy_note(note))
        matches.sort(key=lambda note: note["id"])
        return matches

    def export_json(self):
        notes = [
            {
                "id": note["id"],
                "title": note["title"],
                "body": note["body"],
                "tags": sorted(note["tags"]),
            }
            for note in sorted(self._notes, key=lambda note: note["id"])
        ]
        document = {"schema_version": 1, "notes": notes}
        return json.dumps(
            document,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ) + "\n"

    @staticmethod
    def _copy_note(note):
        return {
            "id": note["id"],
            "title": note["title"],
            "body": note["body"],
            "tags": list(note["tags"]),
        }
