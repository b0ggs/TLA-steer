"""Hidden behavior and static check for canonical-only IDs."""

import argparse
import importlib.util
from pathlib import Path
import sys


FORMAT_ID_REGION = '''def format_id(kind, number):
    """Format an already validated identifier pair."""
    return f"{kind}:{number}"
'''


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(repo):
    path = repo / "src" / "ids.py"
    spec = importlib.util.spec_from_file_location("ids_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/ids.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_rejected(module, value):
    try:
        module.parse_id(value)
    except (TypeError, ValueError):
        return
    raise AssertionError(f"legacy ID was accepted: {value!r}")


def run_checks(repo, module):
    require(
        module.parse_id("user:42") == ("user", 42),
        "canonical user ID changed",
    )
    require(
        module.parse_id("job:007") == ("job", 7),
        "canonical job ID changed",
    )
    expect_rejected(module, "legacy-user:42")
    expect_rejected(module, "legacy-job%3A7")

    source = (repo / "src" / "ids.py").read_text(encoding="utf-8")
    if "_strip_legacy_prefix" in source:
        raise AssertionError("orphaned private legacy helper remains")
    if "urllib.parse" in source or "unquote" in source:
        raise AssertionError("import used only by the legacy helper remains")
    if FORMAT_ID_REGION not in source:
        raise AssertionError("unrelated format_id function changed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    try:
        run_checks(repo, load_module(repo))
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: canonical IDs work and legacy-only code is removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
