"""Entry point so the tool can be run as ``python -m logrotor``."""

import sys

from logrotor.cli import main

if __name__ == "__main__":
    sys.exit(main())
