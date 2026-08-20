"""Demo: normalize and dedupe the bundled sample contacts.

Prints one line per unique contact, then a final summary line of the form
"<N> unique contacts".
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from addrbook import pipeline


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "contacts.json"), encoding="utf-8") as fh:
        records = json.load(fh)
    unique = pipeline.run(records)
    for record in unique:
        print("- {} <{}>".format(record["name"], record["email"]))
    print("{} unique contacts".format(len(unique)))


if __name__ == "__main__":
    main()
