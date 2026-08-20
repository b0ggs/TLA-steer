"""Filter a handful of paths with pathsieve."""

from pathsieve import Sieve, load_text

RULES = """
# build artefacts
*.log
dist
"""


def main():
    sieve = Sieve(load_text(RULES), ignore_case=False)
    for path in ["src/app.py", "dist/app.js", "server.log", "README.md"]:
        marker = "drop" if sieve.excludes(path) else "keep"
        print(marker, path)


if __name__ == "__main__":
    main()
