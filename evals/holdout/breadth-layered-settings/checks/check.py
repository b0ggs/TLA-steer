"""Hidden behavior check for layered settings."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest import mock


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_module(repo):
    path = repo / "src" / "settings.py"
    spec = importlib.util.spec_from_file_location("settings_under_check", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load src/settings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_value_error(action, setting_name):
    try:
        action()
    except ValueError as exc:
        if setting_name not in str(exc):
            raise AssertionError(
                f"ValueError did not identify {setting_name!r}: {exc}"
            ) from exc
    else:
        raise AssertionError(f"expected ValueError identifying {setting_name!r}")


def write_json(directory, name, value):
    path = Path(directory) / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def run_checks(module):
    with mock.patch.dict(os.environ, {}, clear=True):
        require(
            module.load_settings()
            == {"timeout_seconds": 30, "debug": False},
            "defaults are incorrect",
        )

    with tempfile.TemporaryDirectory() as directory:
        valid = write_json(
            directory,
            "valid.json",
            {"timeout_seconds": 45, "debug": True},
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            require(
                module.load_settings(valid)
                == {"timeout_seconds": 45, "debug": True},
                "JSON file did not override defaults",
            )

        with mock.patch.dict(
            os.environ,
            {"APP_TIMEOUT_SECONDS": "90", "APP_DEBUG": "TrUe"},
            clear=True,
        ):
            require(
                module.load_settings(valid)
                == {"timeout_seconds": 90, "debug": True},
                "environment did not override JSON settings",
            )

        with mock.patch.dict(os.environ, {"APP_DEBUG": "false"}, clear=True):
            require(
                module.load_settings(valid)
                == {"timeout_seconds": 45, "debug": False},
                "false environment boolean was not preserved",
            )

        invalid_timeout = write_json(
            directory,
            "invalid-timeout.json",
            {"timeout_seconds": True},
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            expect_value_error(
                lambda: module.load_settings(invalid_timeout),
                "timeout_seconds",
            )

        invalid_debug = write_json(
            directory,
            "invalid-debug.json",
            {"debug": "false"},
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            expect_value_error(lambda: module.load_settings(invalid_debug), "debug")

        unknown = write_json(
            directory,
            "unknown.json",
            {"zeta": 1, "alpha": 2},
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            expect_value_error(lambda: module.load_settings(unknown), "alpha")
            expect_value_error(lambda: module.load_settings(unknown), "zeta")

        not_object = write_json(directory, "list.json", [])
        with mock.patch.dict(os.environ, {}, clear=True):
            expect_value_error(lambda: module.load_settings(not_object), "object")

        with mock.patch.dict(
            os.environ,
            {"APP_TIMEOUT_SECONDS": "not-an-integer"},
            clear=True,
        ):
            expect_value_error(lambda: module.load_settings(), "timeout_seconds")

        with mock.patch.dict(os.environ, {"APP_TIMEOUT_SECONDS": "0"}, clear=True):
            expect_value_error(lambda: module.load_settings(), "timeout_seconds")

        with mock.patch.dict(os.environ, {"APP_DEBUG": "yes"}, clear=True):
            expect_value_error(lambda: module.load_settings(), "debug")

        missing = Path(directory) / "missing.json"
        with mock.patch.dict(os.environ, {}, clear=True):
            try:
                module.load_settings(missing)
            except FileNotFoundError:
                pass
            else:
                raise AssertionError("a supplied missing JSON path must fail")


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

    print("PASS: defaults, file, environment, precedence, and errors are correct")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
