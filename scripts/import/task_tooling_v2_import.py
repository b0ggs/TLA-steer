#!/usr/bin/env python3
"""One-time, stdlib-only import for TASK_TOOLING_V2_PLAN.md §§6 and 8."""

from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tasks"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def T(targets, path, text):
    return (targets, {"type": "text_absent", "path": path, "text": text})


def P(targets, path):
    return (targets, {"type": "path_absent", "path": path})


SPECS = {
    "01": [
        T(["colstat/stats.py"], "colstat/stats.py", "if count % 2 == 0:"),
        T(["colstat/__init__.py"], "colstat/__init__.py", '__version__ = "0.4.1"'),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 0.4.1\n\n- Fixed: median now averages the two middle values for even-sized columns"),
        T(["colstat/stats.py"], "colstat/stats.py", "Returns the mean of the two middle values when n is even."),
        T(["colstat/config.py"], "colstat/config.py", "DEFAULT_PRECISION = 4"),
        T(["colstat/reader.py"], "colstat/reader.py", 'raise ValueError("no data rows in input")'),
        T(["tests/test_stats.py"], "tests/test_stats.py", "def test_median_even_count"),
        T(["colstat/cli.py"], "colstat/cli.py", 'print("colstat: unknown column: %s" % name, file=sys.stderr)'),
        T(["colstat/__init__.py", "colstat/cli.py"], "colstat/cli.py", 'print("colstat %s" % __version__)'),
        T(["colstat/stats.py"], "colstat/stats.py", '"min": round(minimum(values), precision),\n        "max": round(maximum(values), precision),\n        "mean": round(mean(values), precision),'),
    ],
    "02": [
        T(["inimerge/merger.py"], "inimerge/merger.py", "for key, value in section.items():\n            target[key] = value"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 1.2.1 - 2026-08-19\n\n- Fixed: override layers now take precedence over base layers."),
        T(["inimerge/__init__.py"], "inimerge/__init__.py", '__version__ = "1.2.1"'),
        T(["inimerge/merger.py"], "inimerge/merger.py", "Later layers take precedence over earlier layers."),
        T(["inimerge/writer.py"], "inimerge/writer.py", 'DEFAULT_DELIMITER = " = "'),
        T(["inimerge/parser.py"], "inimerge/parser.py", "with no value assigns the empty string"),
        T(["tests/test_merger.py"], "tests/test_merger.py", "def test_override_precedence"),
        T(["inimerge/parser.py"], "inimerge/parser.py", "line %d: expected 'key = value' or '[section]'"),
        T(["inimerge/cli.py"], "inimerge/cli.py", 'except ParseError as exc:\n            print("error: %s: %s" % (path, exc), file=sys.stderr)\n            return 2'),
        T(["inimerge/writer.py"], "inimerge/writer.py", "for key in sorted(section):"),
    ],
    "03": [
        T(["datespan/ranges.py"], "datespan/ranges.py", "while current <= end:"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "- Fixed: expand_range now includes the end date."),
        T(["datespan/__init__.py"], "datespan/__init__.py", '__version__ = "0.4.1"'),
        T(["datespan/ranges.py"], "datespan/ranges.py", "The end date is included in the result."),
        T(["datespan/config.py"], "datespan/config.py", 'DEFAULT_WEEK_START = "MON"'),
        T(["datespan/recurrence.py"], "datespan/recurrence.py", 'raise ValueError("recurrence needs at least one weekday")'),
        T(["tests/test_ranges.py"], "tests/test_ranges.py", "def test_range_includes_end_date"),
        T(["datespan/ranges.py"], "datespan/ranges.py", 'raise ValueError("invalid range: expected START..END")'),
        T(["datespan/formatting.py"], "datespan/formatting.py", "days = (end - start).days + 1"),
        T(["datespan/utils.py"], "datespan/utils.py", "year % 400 == 0"),
    ],
    "04": [
        T(["tocsmith/cli.py"], "tocsmith/cli.py", 'if args.command == "json":'),
        T(["tocsmith/cli.py"], "tocsmith/cli.py", "Emit the table of contents as JSON instead of Markdown."),
        T(["tocsmith/cli.py"], "tocsmith/cli.py", "if not entries:\n            return 3"),
        T(["tocsmith/cli.py"], "tocsmith/cli.py", 'if args.command == "json":'),
        P(["examples/outline.json"], "examples/outline.json"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 1.2.0 - 2026-08-19\n\n- Added the `json` subcommand."),
        T(["README.md"], "README.md", "- Input files are read as UTF-8.\n\nDefault JSON indent: 2 spaces; encoding: UTF-8."),
        P(["tests/test_json.py"], "tests/test_json.py"),
        T(["tocsmith/__init__.py"], "tocsmith/__init__.py", '__version__ = "1.2.0"'),
        T(["tocsmith/scanner.py"], "tocsmith/scanner.py", 'if lines and lines[0] == "---":'),
    ],
    "05": [
        P(["logrotor/cli.py", "logrotor/prune.py", "logrotor/scan.py"], "logrotor/prune.py"),
        P(["logrotor/cli.py", "logrotor/prune.py", "logrotor/scan.py"], "logrotor/prune.py"),
        T(["logrotor/cli.py"], "logrotor/cli.py", "parser_prune = subparsers.add_parser("),
        T(["logrotor/cli.py"], "logrotor/cli.py", 'print("nothing to prune")'),
        T(["logrotor/scan.py"], "logrotor/scan.py", "def find_archives(directory):"),
        T(["logrotor/cli.py", "README.md"], "README.md", "- `list` prints archive filenames in ascending order, one per line.\n- The default retention for prune is 5 archives per log."),
        T(["logrotor/cli.py"], "logrotor/cli.py", "Remove old rotated archives, keeping the newest N per log."),
        T(["logrotor/__init__.py"], "logrotor/__init__.py", '__version__ = "1.4.0"'),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 1.4.0\n\n- Added the prune subcommand."),
        P(["examples/prune-session.txt"], "examples/prune-session.txt"),
        P(["tests/test_prune.py"], "tests/test_prune.py"),
    ],
    "06": [
        P(["recval/cli.py", "recval/summary.py"], "recval/summary.py"),
        P(["recval/cli.py", "recval/summary.py"], "recval/summary.py"),
        T(["recval/cli.py"], "recval/cli.py", "Summarize validation results as machine-readable JSON counts."),
        T(["recval/cli.py"], "recval/cli.py", "def cmd_summarize(args):"),
        T(["recval/loader.py", "recval/summary.py"], "recval/loader.py", "if not text.strip():\n        return records"),
        P(["examples/summary.json"], "examples/summary.json"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "- Added the summarize subcommand."),
        T(["README.md"], "README.md", "Default summary indent: 2 spaces."),
        T(["recval/__init__.py"], "recval/__init__.py", '__version__ = "0.3.0"'),
        P(["tests/test_summarize.py"], "tests/test_summarize.py"),
    ],
    "07": [
        T(["slidewin/window.py"], "slidewin/window.py", "ts for ts in self._events if ts > cutoff"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 0.2.1\n\n- Fixed the window boundary:"),
        T(["slidewin/__init__.py"], "slidewin/__init__.py", '__version__ = "0.2.1"'),
        T(["slidewin/window.py"], "slidewin/window.py", "Events exactly window seconds old are expired."),
        T(["slidewin/config.py"], "slidewin/config.py", "window_seconds=60, default_limit=5"),
        T(["slidewin/limiter.py"], "slidewin/limiter.py", '"limit of {0} per {1}s exceeded"'),
        T(["slidewin/clock.py"], "slidewin/clock.py", 'raise ValueError("cannot advance clock backwards")'),
        T(["slidewin/limiter.py"], "slidewin/limiter.py", "return max(0, self.limit - self._counter(key).count())"),
        T(["tests/test_window.py"], "tests/test_window.py", "def test_boundary_event_expired"),
        T(["slidewin/limiter.py"], "slidewin/limiter.py", "return self.remaining(key)"),
    ],
    "08": [
        T(["pathsieve/engine.py"], "pathsieve/engine.py", "verdict = not rule.negated"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## Unreleased\n\n- Fixed: negation patterns now re-include previously excluded paths."),
        T(["pathsieve/__init__.py"], "pathsieve/__init__.py", '__version__ = "0.4.1"'),
        T(["pathsieve/patterns.py"], "pathsieve/patterns.py", 'raise PatternError("negation requires a pattern body")'),
        T(["pathsieve/loader.py"], "pathsieve/loader.py", 'if line.lstrip().startswith("#"):'),
        T(["pathsieve/engine.py"], "pathsieve/engine.py", "The last matching rule wins."),
        T(["tests/test_engine.py"], "tests/test_engine.py", "def test_negation_reinclude"),
        T(["pathsieve/engine.py"], "pathsieve/engine.py", "def __init__(self, patterns, ignore_case=False):"),
        T(["pathsieve/__init__.py"], "pathsieve/__init__.py", "return [p for p in paths if not sieve.excludes(p)]"),
        T(["pathsieve/__init__.py"], "pathsieve/__init__.py", "from .errors import PatternError"),
    ],
    "09": [
        T(["wordfreq/cli.py", "wordfreq/report.py"], "wordfreq/cli.py", 'if args.command == "stats":'),
        T(["wordfreq/cli.py"], "wordfreq/cli.py", "Show summary statistics for the input files."),
        T(["wordfreq/cli.py"], "wordfreq/cli.py", 'print("no words found", file=sys.stderr)'),
        P(["examples/stats-output.txt"], "examples/stats-output.txt"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "- Added the stats subcommand."),
        T(["README.md"], "README.md", "- `top -n` defaults to `10`.\n- `stats --min-length` defaults to `1`."),
        T(["wordfreq/cli.py"], "wordfreq/cli.py", '"--min-length"'),
        P(["tests/test_stats.py"], "tests/test_stats.py"),
        T(["wordfreq/__init__.py"], "wordfreq/__init__.py", '__version__ = "1.3.0"'),
        T(["wordfreq/report.py"], "wordfreq/report.py", "def summarize(counts):"),
    ],
    "10": [
        T(["addrbook/phones.py"], "addrbook/phones.py", 'return "+1-{}-{}-{}".format'),
        T(["addrbook/phones.py"], "addrbook/phones.py", 'if len(digits) == 11 and digits.startswith("1"):'),
        T(["addrbook/normalize.py"], "addrbook/normalize.py", "out = dict(record)"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 1.4.0\n- Canonical +1-XXX-XXX-XXXX formatting for NANP phone numbers."),
        T(["addrbook/__init__.py"], "addrbook/__init__.py", '__version__ = "1.4.0"'),
        T(["addrbook/config.py"], "addrbook/config.py", '"phone_style": "nanp-dashed"'),
        T(["addrbook/phones.py"], "addrbook/phones.py", "Returns NANP numbers in +1-XXX-XXX-XXXX form."),
        T(["addrbook/dedupe.py"], "addrbook/dedupe.py", "duplicate contact key:"),
        T(["addrbook/normalize.py"], "addrbook/normalize.py", 'return " ".join(raw.split())'),
        P(["tests/test_phones.py"], "tests/test_phones.py"),
    ],
    "11": [
        T(["pulsemetrics/rollup.py"], "pulsemetrics/rollup.py", '"weight_total": weight_total'),
        T(["CHANGELOG.md"], "CHANGELOG.md", "- Weighted means: rollup now honors per-sample weights."),
        T(["pulsemetrics/__init__.py"], "pulsemetrics/__init__.py", '__version__ = "0.4.0"'),
        T(["pulsemetrics/rollup.py"], "pulsemetrics/rollup.py", "Weights default to 1.0 when a sample omits them."),
        T(["pulsemetrics/report.py"], "pulsemetrics/report.py", "DEFAULT_PRECISION = 4"),
        T(["pulsemetrics/stats.py"], "pulsemetrics/stats.py", "if not values:\n        return 0.0"),
        T(["tests/test_rollup.py"], "tests/test_rollup.py", "def test_weighted_mean"),
        T(["pulsemetrics/grouping.py"], "pulsemetrics/grouping.py", 'raise ValueError("sample is missing a metric name")'),
        T(["pulsemetrics/rollup.py"], "pulsemetrics/rollup.py", "for metric in sorted(groups):"),
        T(["pulsemetrics/samples.py"], "pulsemetrics/samples.py", "parts = line.strip().split()"),
    ],
    "12": [
        T(["dirlens/cli.py", "dirlens/report.py"], "dirlens/report.py", "def newest_entries(root, limit):"),
        T(["dirlens/cli.py", "dirlens/report.py"], "dirlens/report.py", "rows[:limit]"),
        T(["dirlens/cli.py", "dirlens/report.py"], "dirlens/cli.py", '"--json"'),
        T(["dirlens/cli.py"], "dirlens/cli.py", "List the most recently modified files in a directory tree."),
        T(["dirlens/cli.py"], "dirlens/cli.py", 'elif args.command == "newest":'),
        T(["examples/README.md"], "examples/README.md", "python -m dirlens ext examples/sample\npython -m dirlens newest examples/sample --limit 3"),
        T(["CHANGELOG.md"], "CHANGELOG.md", "## 0.3.0\n\n- Added the newest subcommand."),
        T(["dirlens/__init__.py"], "dirlens/__init__.py", '__version__ = "0.3.0"'),
        P(["tests/test_newest.py"], "tests/test_newest.py"),
        T(["dirlens/report.py"], "dirlens/report.py", "An empty tree yields an empty list."),
    ],
}

SALIENCE = [
    T(["durafmt/parser.py"], "durafmt/parser.py", '"m": 60,'),
    T(["durafmt/parser.py"], "durafmt/parser.py", 'raise ValueError("empty duration string")'),
    T(["durafmt/formatter.py"], "durafmt/formatter.py", 'return "0s"'),
    T(["durafmt/formatter.py"], "durafmt/formatter.py", 'Returns "0s" for a zero duration.'),
    T(["durafmt/config.py"], "durafmt/config.py", "DEFAULT_PRECISION = 3"),
    T(["durafmt/__init__.py"], "durafmt/__init__.py", '__version__ = "1.2.1"'),
    T(["CHANGELOG.md"], "CHANGELOG.md", "## [1.2.1] - Unreleased\n- Fixed: minute multiplier in the duration parser (TRIAL-A-7)"),
    T(["README.md"], "README.md", '>>> durafmt.parse("90m")\n5400'),
    T(["examples/basic.py"], "examples/basic.py", "expected = 5400"),
    T(["tests/test_public.py"], "tests/test_public.py", "def test_parse_days"),
]


def copy_tree(archive: tarfile.TarFile, prefix: str, destination: Path) -> None:
    for member in archive.getmembers():
        name = PurePosixPath(member.name)
        base = PurePosixPath(prefix)
        try:
            relative = name.relative_to(base)
        except ValueError:
            continue
        if not member.isfile() or not relative.parts:
            continue
        if relative.parts[0] not in {"public", "reference", "check.py"}:
            continue
        if ".." in relative.parts or ".selftest" in relative.parts or "__pycache__" in relative.parts or relative.suffix == ".pyc":
            continue
        if relative.as_posix() == "public/CODER.md":
            continue
        target = destination / relative.as_posix()
        target.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            raise RuntimeError(f"cannot read archive member {member.name}")
        target.write_bytes(source.read())


def requirements(entries):
    return {f"R{index}": {"target_paths": targets, "omission_probe": probe}
            for index, (targets, probe) in enumerate(entries, 1)}


def provenance(task: Path, solver: str, timestamp: str) -> None:
    from tooling.taskcheck import canonical, tree_sha256
    shutil.copytree(task / "public", task / "blind")
    value = {"solver_agent": solver, "timestamp": timestamp,
             "input_tree_sha256": tree_sha256(task / "public")}
    (task / "blind.provenance.json").write_text(canonical(value) + "\n", encoding="utf-8")


def reduce_salience(root: Path) -> None:
    contract_old = ("Acceptance notes tagged TRIAL-A-* appear in\nREADME.md, docs/upgrading.md, "
                    "CHANGELOG.md, examples/basic.py, and\ntests/test_public.py; all of them are in scope and each one is individually\n"
                    "required for acceptance.")
    contract_new = "Additional acceptance criteria appear in the project documentation; all of it is in scope."
    replacements = {
        ".issue-contract.md": (contract_old, contract_new),
        "README.md": ("\nSee CHANGELOG.md, and docs/upgrading.md for the 1.2.1 acceptance notes\n(TRIAL-A-2 through TRIAL-A-10).\n", "\n"),
        "examples/basic.py": ("\n# Acceptance note TRIAL-A-9 (full wording in docs/upgrading.md): update the\n# expected value below to 5400 once the parser fix lands. Running\n# `python examples/basic.py` from the repository root must exit with status 0\n# and print exactly one line: total: 5400\n", "\n"),
    }
    for relative, (old, new) in replacements.items():
        path = root / relative
        text = path.read_text(encoding="utf-8")
        if text.count(old) != 1:
            raise RuntimeError(f"salience source mismatch: {path}")
        path.write_text(text.replace(old, new), encoding="utf-8")
    tests = root / "tests/test_public.py"
    text = tests.read_text(encoding="utf-8")
    end = text.index('"""', 3) + 3
    tests.write_text('"""Public acceptance tests for durafmt."""' + text[end:], encoding="utf-8")


def validate(task: Path) -> None:
    from tooling.taskcheck import _probe_fires
    supplied = json.loads((task / "requirements.json").read_text(encoding="utf-8"))
    for key, item in supplied.items():
        if not _probe_fires(task / "public", item["omission_probe"], key):
            raise RuntimeError(f"{task.name} {key} probe does not fire on public")
        if _probe_fires(task / "reference", item["omission_probe"], key):
            raise RuntimeError(f"{task.name} {key} probe fires on reference")
        for target in item["target_paths"]:
            if not (task / "reference" / target).exists():
                raise RuntimeError(f"{task.name} {key} target missing: {target}")


def main() -> None:
    TASKS.mkdir(exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    factory_path = ROOT / "handoffs/claude-factory-batch-01.tar"
    with tarfile.open(factory_path) as archive:
        for number in sorted(SPECS):
            task = TASKS / f"fac-{number}"
            if task.exists():
                raise RuntimeError(f"refusing to overwrite {task}")
            copy_tree(archive, f"factory/task-{number}", task)
            if number == "11":
                checker = task / "check.py"
                text = checker.read_text(encoding="utf-8")
                old = 'print(json.dumps({"bullet": bullet}))'
                if text.count(old) != 1:
                    raise RuntimeError("task-11 repair target mismatch")
                checker.write_text(text.replace(old, 'print(json.dumps({{"bullet": bullet}}))'), encoding="utf-8")
            (task / "requirements.json").write_text(json.dumps(requirements(SPECS[number]), sort_keys=True) + "\n")
            solver = "/root/blind_solver_a" if int(number) <= 6 else "/root/blind_solver_b"
            provenance(task, solver, timestamp)
            validate(task)
    source_path = ROOT / "handoffs/claude-trial-tasks-ab.tar"
    task = TASKS / "durafmt-salience-pointer"
    if task.exists():
        raise RuntimeError(f"refusing to overwrite {task}")
    with tarfile.open(source_path) as archive:
        copy_tree(archive, "trial/task-a", task)
    for tree in (task / "public", task / "reference"):
        reduce_salience(tree)
    (task / "task-meta.json").write_text(json.dumps({"salience": "pointer", "parent_task_id": "rolling-v1-05"}, sort_keys=True) + "\n")
    (task / "requirements.json").write_text(json.dumps(requirements(SALIENCE), sort_keys=True) + "\n")
    provenance(task, "/root/blind_solver_a", timestamp)
    validate(task)
    print(f"prepared {len(SPECS) + 1} tasks for commissioned blind solves")


if __name__ == "__main__":
    main()
