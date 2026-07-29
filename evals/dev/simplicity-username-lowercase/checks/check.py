"""Hidden behavior check for username normalization."""

import argparse
import importlib.util
from pathlib import Path
import sys


def load_module(repo):
    path = repo / "src" / "usernames.py"
    spec = importlib.util.spec_from_file_location("usernames_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/usernames.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    examples = {
        "Alice": "alice",
        "  BOB  ": "bob",
        "\tMiXeD-123\n": "mixed-123",
        "already_lower": "already_lower",
        "": "",
    }

    try:
        module = load_module(repo)
        for value, wanted in examples.items():
            actual = module.normalize_username(value)
            if actual != wanted:
                raise AssertionError(
                    f"normalize_username({value!r}) returned {actual!r}, wanted {wanted!r}"
                )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: usernames are stripped and lowercased")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
