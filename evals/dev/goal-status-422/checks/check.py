"""Hidden behavior check for validation-error status mapping."""

import argparse
import importlib.util
from pathlib import Path
import sys


def load_module(repo):
    path = repo / "src" / "statuses.py"
    spec = importlib.util.spec_from_file_location("statuses_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/statuses.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks(module):
    expected = {
        "validation_error": 422,
        "not_found": 404,
        "conflict": 409,
        "unexpected": 500,
    }
    for error_kind, wanted in expected.items():
        actual = module.status_for_error(error_kind)
        if actual != wanted:
            raise AssertionError(
                f"status_for_error({error_kind!r}) returned {actual}, wanted {wanted}"
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

    print("PASS: validation maps to 422 and all other statuses are preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
