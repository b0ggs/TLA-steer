#!/usr/bin/env python3
"""Objective checker for scout-b-refactor-data-01."""

import argparse
import dataclasses
import importlib
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
TASK_ID = "scout-b-refactor-data-01"
EXPECTED_CONTRACT = """# Freeze inventory rows while preserving mapping compatibility

Refactor the repository's internal row representation without removing its
public mapping conversion behavior.

## Main request

### R1 — Frozen row representation

Replace `InventoryRow` in `src/stock_rows/model.py` with a frozen dataclass whose fields, in order, are `sku: str`, `quantity: int`, and `labels: tuple[str, ...] = ()`.

Seven secondary requirements are distributed beside the affected conversion,
merge, serialization, and documentation components. The public notes marked R2
through R8 are all part of this task. The README statement marked G1 is a
regression constraint.
"""
EXPECTED_README = """# Stock rows

The package converts inventory mappings, merges rows, and writes JSON.

## Compatibility

G1 — `row_to_mapping(row)` without a `quantity_key` argument must remain compatible by emitting the key `quantity` and a list-valued `labels` field.
"""
EXPECTED_INIT = """\"\"\"Inventory-row conversion package.\"\"\"

from .convert import row_from_mapping, row_to_mapping
from .io import dump_rows
from .merge import merge_rows
from .model import InventoryRow

__all__ = [
    \"InventoryRow\",
    \"dump_rows\",
    \"merge_rows\",
    \"row_from_mapping\",
    \"row_to_mapping\",
]
"""
EXPECTED_FILES = (".issue-contract.md", "CODER.md", "CHANGELOG.md", "README.md", "config/fields.json", "docs/data-model.md", "docs/output-format.md", "src/stock_rows/__init__.py", "src/stock_rows/convert.py", "src/stock_rows/io.py", "src/stock_rows/merge.py", "src/stock_rows/model.py")


def assertion(function):
    try:
        function()
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_package(root):
    sys.path.insert(0, str(root / "src"))
    for name in tuple(sys.modules):
        if name == "stock_rows" or name.startswith("stock_rows."):
            sys.modules.pop(name, None)
    return importlib.import_module("stock_rows")


def check(root):
    environment = assertion(lambda: require(all((root / path).is_file() for path in EXPECTED_FILES) and not (root / "check.py").exists(), "public packet shape invalid"))
    try:
        stock = load_package(root)
        load_error = None
    except Exception as exc:
        stock = None
        load_error = exc

    def loaded():
        if load_error is not None:
            raise load_error

    def r1():
        loaded()
        cls = stock.InventoryRow
        require(dataclasses.is_dataclass(cls), "InventoryRow is not a dataclass")
        fields = dataclasses.fields(cls)
        require([field.name for field in fields] == ["sku", "quantity", "labels"], "field order differs")
        require([field.type for field in fields] == [str, int, tuple[str, ...]] and fields[2].default == (), "annotations/default differ")
        require(cls.__dataclass_params__.frozen is True, "dataclass is not frozen")
        row = cls("A", 1)
        try:
            row.quantity = 2
        except dataclasses.FrozenInstanceError:
            return
        raise AssertionError("row assignment succeeded")

    def r2():
        loaded()
        require(stock.row_from_mapping({"sku": "A", "qty": 2}).quantity == 2, "legacy qty is not accepted")
        require(stock.row_from_mapping({"sku": "A", "quantity": 3, "qty": 2}).quantity == 3, "quantity precedence differs")

    def r3():
        loaded()
        labels = ["z", "a"]
        data = {"sku": "A", "quantity": 1, "labels": labels}
        snapshot = {"sku": "A", "quantity": 1, "labels": ["z", "a"]}
        row = stock.row_from_mapping(data)
        require(row.labels == ("a", "z"), "labels are not a sorted tuple")
        require(data == snapshot and data["labels"] is labels, "input mapping/list changed")

    def r4():
        loaded()
        try:
            stock.row_from_mapping({"sku": "A", "quantity": -1})
        except ValueError:
            pass
        else:
            raise AssertionError("negative quantity was accepted")
        require(stock.row_from_mapping({"sku": "A", "quantity": 0}).quantity == 0, "zero quantity was rejected")

    def r5():
        loaded()
        rows = [stock.InventoryRow("B", 1, ("x",)), stock.InventoryRow("A", 2, ("z",)), stock.InventoryRow("B", 3, ("y",))]
        require(stock.merge_rows(rows) == [stock.InventoryRow("B", 4, ("x",)), stock.InventoryRow("A", 2, ("z",))], "duplicate merge/order/labels differ")

    def r6():
        loaded()
        config = json.loads((root / "config/fields.json").read_text(encoding="utf-8"))
        require(config == {"output_quantity_key": "count"}, "configured quantity key differs")
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "rows.json"
            stock.dump_rows([stock.InventoryRow("A", 2, ("red",))], output, root / "config/fields.json")
            text = output.read_text(encoding="utf-8")
            require(json.loads(text) == [{"sku": "A", "count": 2, "labels": ["red"]}], "serialized payload differs")
            require(text.endswith("\n") and text.count("\n") == 1, "serialized newline differs")

    def r7():
        lines = (root / "docs/data-model.md").read_text(encoding="utf-8").splitlines()
        require(lines.count("## Frozen row model") == 1, "frozen-model heading missing")
        start = lines.index("## Frozen row model") + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
        section = lines[start:end]
        require(section.count("InventoryRow instances are immutable.") == 1, "immutability sentence missing")
        require(section.count("Legacy input may use qty; serialized output uses the configured quantity key.") == 1, "compatibility sentence missing")

    def r8():
        lines = (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        bullet = "- Refactored inventory rows to an immutable representation."
        require(lines.count(bullet) == 1 and lines.index(bullet) > lines.index("## Unreleased"), "changelog bullet missing")

    def g1():
        loaded()
        row = stock.InventoryRow("A", 2, ("red",))
        require(stock.row_to_mapping(row) == {"sku": "A", "quantity": 2, "labels": ["red"]}, "mapping compatibility regressed")

    def integrity_check():
        require((root / "CODER.md").read_bytes() == b"", "CODER.md changed")
        require((root / ".issue-contract.md").read_text(encoding="utf-8") == EXPECTED_CONTRACT, "contract changed")
        require((root / "README.md").read_text(encoding="utf-8") == EXPECTED_README, "README compatibility changed")
        require((root / "src/stock_rows/__init__.py").read_text(encoding="utf-8") == EXPECTED_INIT, "package exports changed")

    requirements = {name: assertion(func) for name, func in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4), ("R5", r5), ("R6", r6), ("R7", r7), ("R8", r8))}
    regressions = {"G1": assertion(g1)}
    integrity = assertion(integrity_check)
    resolved = environment["passed"] and integrity["passed"] and all(item["passed"] for item in requirements.values()) and all(item["passed"] for item in regressions.values())
    return {"environment": environment, "integrity": integrity, "regressions": regressions, "requirements": requirements, "resolved": resolved, "schema": "scout-check-result-v1", "task_id": TASK_ID}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.workspace.resolve()), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
