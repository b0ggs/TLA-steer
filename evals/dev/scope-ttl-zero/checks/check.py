"""Hidden behavior check for zero-TTL cache entries."""

import argparse
import importlib.util
from pathlib import Path
import sys


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def load_module(repo):
    path = repo / "src" / "cache.py"
    spec = importlib.util.spec_from_file_location("cache_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/cache.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks(module):
    clock = Clock()
    cache = module.Cache(clock)
    cache.set("forever", "value", 0)
    clock.now += 1_000_000
    require(cache.get("forever") == "value", "TTL 0 entry expired")

    clock = Clock()
    cache = module.Cache(clock)
    cache.set("short", "value", 5)
    clock.now += 4.999
    require(cache.get("short") == "value", "positive TTL expired early")
    clock.now += 0.001
    require(cache.get("short") is None, "positive TTL did not expire")

    clock = Clock()
    cache = module.Cache(clock)
    cache.set(" legacy::key ", "legacy-value", 0)
    clock.now += 100
    require(cache.get("key") == "legacy-value", "legacy normalization changed")


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

    print("PASS: zero and positive TTL behavior is correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
