"""Allow running the package with `python -m recval`."""
import sys

from .cli import main

sys.exit(main())
