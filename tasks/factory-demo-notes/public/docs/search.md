# Search matching

The query match must be case-insensitive using Unicode case folding, must look for the query as a substring of either title or body, and must treat an empty query as unrestricted.

Tag filters must trim surrounding whitespace, compare by Unicode case folding, require every requested tag to be present, and treat None or an empty iterable as unrestricted.

Tags are matched without changing the strings stored on the note.
