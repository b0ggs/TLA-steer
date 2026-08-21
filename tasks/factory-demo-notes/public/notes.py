"""A tiny in-memory notes collection."""


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

    @staticmethod
    def _copy_note(note):
        return {
            "id": note["id"],
            "title": note["title"],
            "body": note["body"],
            "tags": list(note["tags"]),
        }
