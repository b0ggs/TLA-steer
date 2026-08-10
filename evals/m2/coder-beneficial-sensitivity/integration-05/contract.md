# Directory checksum manifest

Update `solution.py` so that it satisfies all of the following requirements:

- Given a directory, emit sorted lines of lowercase SHA-256, two spaces, and each relative POSIX file path.
- Include regular files recursively but exclude hidden files and anything beneath a hidden directory.
- With --verify MANIFEST DIRECTORY, exit 0 only when the current manifest matches exactly, otherwise exit 1 with a concise stderr message.

Regression constraint: Hash file bytes rather than decoded text, and emit no output for an empty directory.

