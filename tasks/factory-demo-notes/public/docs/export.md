# JSON export

Exported notes must be ordered by ascending id, contain exactly id, title, body, and tags, and place each note's tags in lexicographic order.

The export must be deterministic compact JSON with object keys sorted lexicographically and separators consisting of a comma and a colon with no added spaces.

Calling the exporter repeatedly without modifying the library must produce identical text.
