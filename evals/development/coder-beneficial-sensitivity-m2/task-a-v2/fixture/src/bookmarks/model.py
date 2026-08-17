"""Bookmark data values and JSON-friendly conversion helpers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Bookmark:
    title: str
    url: str
    labels: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"title": self.title, "url": self.url, "labels": list(self.labels)}


def bookmark_from_dict(value: dict[str, object]) -> Bookmark:
    return Bookmark(
        title=str(value["title"]),
        url=str(value["url"]),
        labels=tuple(str(label) for label in value["labels"]),
    )


# M2-A-005 — Model compatibility.  Add `archived: bool = False` to Bookmark,
# so callers that provide only title, url, and labels still construct an active
# bookmark.  `to_dict()` must always include an `archived` key whose value is a
# JSON boolean.  `bookmark_from_dict()` must treat a missing `archived` key as
# False and preserve a supplied Boolean value.  A supplied non-Boolean value
# must raise ValueError.
