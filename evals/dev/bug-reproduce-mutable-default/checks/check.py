"""Hidden behavior check for mutable-default isolation."""

import argparse
import importlib.util
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(repo):
    path = repo / "src" / "tags.py"
    spec = importlib.util.spec_from_file_location("tags_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/tags.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks(module):
    require(module.merge_tags(["alpha"]) == ["alpha"], "first default call is wrong")
    require(
        module.merge_tags(["beta"]) == ["beta"],
        "default state leaked across calls",
    )
    require(module.merge_tags([]) == [], "empty default call inherited prior state")

    explicit = ["existing"]
    result = module.merge_tags(["new"], explicit)
    require(result is explicit, "explicit accumulator was replaced")
    require(
        explicit == ["existing", "new"],
        "explicit accumulator was not extended",
    )

    require(
        module.merge_tags(["final"]) == ["final"],
        "explicit and default calls contaminated one another",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    try:
        run_checks(load_module(repo))
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: default calls are isolated and explicit accumulation still works")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
