"""Hidden behavior check for the repository-resolved duration format."""

import argparse
import importlib.util
from pathlib import Path
import sys


def load_module(repo):
    path = repo / "src" / "duration.py"
    spec = importlib.util.spec_from_file_location("duration_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/duration.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    expected = {
        0: "0 min",
        59: "59 min",
        60: "1h 00m",
        65: "1h 05m",
        125: "2h 05m",
    }

    try:
        module = load_module(repo)
        for minutes, wanted in expected.items():
            actual = module.display_duration(minutes)
            if actual != wanted:
                raise AssertionError(
                    f"display_duration({minutes}) returned {actual!r}, wanted {wanted!r}"
                )
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: compact duration behavior follows ADR-004")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
