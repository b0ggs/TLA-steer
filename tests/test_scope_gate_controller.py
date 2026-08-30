from __future__ import annotations

import base64
import json
from pathlib import Path
import sys

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import scope_gate_controller as controller  # noqa: E402


SCOPE_GATE = PROJECT_ROOT / ".scope-gate-venv/bin/scope-gate"
CHECK_IDS = ("check-focused-tests", "check-offline-report")


def _contract() -> dict:
    contract = {
        "schema_version": "scope-gate-contract-v1",
        "scope_revision": "TEST-TASK-r1",
        "approved_requirements": [
            {
                "id": "REQ-TEST",
                "mapped_check_ids": ["check-focused-tests"],
            }
        ],
        "approved_invariants": [
            {
                "id": "INV-TEST",
                "mapped_check_ids": ["check-offline-report"],
            }
        ],
        "excluded_capability_ids": ["CAP-NOT-REQUESTED"],
        "allowed_path_patterns": ["src/**"],
        "checks": [
            {
                "id": "check-focused-tests",
                "definition": "Run the accepted focused tests; pass only on exit 0.",
            },
            {
                "id": "check-offline-report",
                "definition": "Run the accepted offline report; pass only on exit 0.",
            },
        ],
    }
    contract["canonical_digest"] = controller.contract_digest(contract, SCOPE_GATE)
    return contract


def _frozen_task(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    contract_path = root / ".scope-gate/contracts/task.json"
    contract_path.parent.mkdir(parents=True)
    contract_path.write_bytes(controller.canonical_bytes(_contract()))
    state_path = tmp_path / "controller-state.json"
    controller.begin(
        root=root,
        contract_path=contract_path,
        state_path=state_path,
        executable=SCOPE_GATE,
    )
    return root, state_path


def _change(root: Path, relative_path: str = "src/example.py") -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("VALUE = 1\n", encoding="utf-8")


def _runner(failed: set[str] | None = None):
    failures = failed or set()
    return lambda check_id: 1 if check_id in failures else 0


def _evaluate(root: Path, state_path: Path, *, findings=None, failed=None):
    return controller.evaluate(
        root=root,
        state_path=state_path,
        findings=[] if findings is None else findings,
        executable=SCOPE_GATE,
        check_runner=_runner(failed),
    )


def _rewrite_state(state_path: Path, mutation: str) -> None:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if mutation == "digest":
        contract = json.loads(base64.b64decode(state["contract_b64"]))
        contract["canonical_digest"] = "0" * 64
        state["contract_b64"] = base64.b64encode(
            controller.canonical_bytes(contract)
        ).decode("ascii")
    elif mutation == "revision":
        state["expected_scope_revision"] = "TEST-TASK-r2"
    else:  # pragma: no cover - test helper guard
        raise AssertionError(mutation)
    state_path.chmod(0o600)
    state_path.write_bytes(controller.canonical_bytes(state))


def test_allowed_path_and_passing_checks_succeeds(tmp_path: Path) -> None:
    root, state_path = _frozen_task(tmp_path)
    _change(root)

    exit_code, report = _evaluate(root, state_path)

    assert exit_code == 0
    assert report["scope_gate_exit"] == 0
    assert report["completion_allowed"] is True
    assert report["changes"]["changed_paths"] == ["src/example.py"]


@pytest.mark.parametrize(
    "finding",
    [
        {
            "id": "F-INVENTED",
            "subject_type": "requirement",
            "subject_id": "REQ-INVENTED",
            "check_ids": ["check-focused-tests"],
        },
        {
            "id": "F-EXCLUDED",
            "subject_type": "capability",
            "subject_id": "CAP-NOT-REQUESTED",
            "check_ids": [],
        },
        {
            "id": "F-UNMAPPED",
            "subject_type": "requirement",
            "subject_id": "REQ-TEST",
            "check_ids": ["check-offline-report"],
        },
    ],
)
def test_advisory_finding_does_not_dispatch_work(
    tmp_path: Path, finding: dict
) -> None:
    root, state_path = _frozen_task(tmp_path)
    _change(root)
    before = controller.repository_manifest(root)

    exit_code, report = _evaluate(root, state_path, findings=[finding])

    assert exit_code == 0
    assert report["scope_gate_exit"] == 0
    assert report["evaluation"]["disposition"] == "advisory"
    assert controller.repository_manifest(root) == before


def test_mapped_trusted_failure_blocks(tmp_path: Path) -> None:
    root, state_path = _frozen_task(tmp_path)
    _change(root)
    finding = {
        "id": "F-MAPPED",
        "subject_type": "requirement",
        "subject_id": "REQ-TEST",
        "check_ids": ["check-focused-tests"],
    }

    exit_code, report = _evaluate(
        root,
        state_path,
        findings=[finding],
        failed={"check-focused-tests"},
    )

    assert exit_code == 2
    assert report["scope_gate_exit"] == 2
    assert report["evaluation"]["disposition"] == "block"


def test_out_of_allowlist_path_blocks(tmp_path: Path) -> None:
    root, state_path = _frozen_task(tmp_path)
    _change(root, "README.md")

    exit_code, report = _evaluate(root, state_path)

    assert exit_code == 2
    assert report["scope_gate_exit"] == 2
    assert report["evaluation"]["reason_codes"] == [
        "changed_path_outside_allowlist"
    ]


@pytest.mark.parametrize("mutation", ["digest", "revision"])
def test_contract_integrity_mismatch_blocks(tmp_path: Path, mutation: str) -> None:
    root, state_path = _frozen_task(tmp_path)
    _change(root)
    _rewrite_state(state_path, mutation)

    exit_code, report = _evaluate(root, state_path)

    assert exit_code == 2
    assert report["scope_gate_exit"] == 2
    assert report["evaluation"]["disposition"] == "block"


def test_malformed_bundle_is_exit_three_and_fails_closed() -> None:
    with pytest.raises(controller.IntegrationError) as raised:
        controller.invoke_evaluate(
            {"schema_version": "scope-gate-bundle-v1"}, SCOPE_GATE
        )

    assert raised.value.scope_gate_exit == 3


def test_failed_required_check_without_finding_refuses_completion(
    tmp_path: Path,
) -> None:
    root, state_path = _frozen_task(tmp_path)
    _change(root)

    exit_code, report = _evaluate(
        root,
        state_path,
        failed={"check-offline-report"},
    )

    assert report["scope_gate_exit"] == 0
    assert report["evaluation"]["disposition"] == "advisory"
    assert exit_code == 2
    assert report["completion_allowed"] is False
