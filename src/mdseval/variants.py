"""Locked variant construction and runtime integrity checks."""

from __future__ import annotations

from pathlib import Path

from .hashing import sha256_file

CHAMPION_SHA256 = "e72791366f3a3c20780a3ece63b0b8c1a0b7862c7c5ffd1d8ea8d3dd6eed92b0"
INSERTION_ANCHOR = (
    "5. Create the authorized review handoff (PR, review ref, or explicitly "
    "approved branch-only/draft/candidate artifact) when the issue is "
    "handoff-ready and the workflow authorizes publication\n"
)
CANDIDATE_BLOCK = """
## Implementation Discipline

Before editing:

- Resolve consequential ambiguity. Inspect repository evidence first. If two
  plausible interpretations remain and choosing the wrong one changes required
  behavior, stop and ask one focused question. Do not ask when the issue
  contract or repository evidence resolves it.
- Choose the smallest implementation that fully satisfies the issue contract.
  Avoid speculative abstractions, unrequested configurability, and adjacent
  refactoring.
- Keep every changed line traceable to a requirement, a test, or cleanup made
  necessary by your own change. Remove imports or private helpers made orphaned
  by your change, but leave unrelated cleanup alone.
- For a bug fix, reproduce the failure before editing when a runnable
  reproduction exists, then verify the same behavior after the fix. For a clear
  feature request, do not invent a reproduction ritual; implement it and run
  the relevant acceptance checks.
"""
BAD_CONTROL_BLOCK = """
## Implementation Discipline

- When the issue contract leaves implementation structure or extension points
  open, prefer a reusable, caller-configurable abstraction over direct logic,
  even when only one behavior is currently required.
- For duration-formatting work, model the format as a configurable object
  accepted by `display_duration`.
- For TTL work, make the non-expiring sentinel configurable through the `Cache`
  constructor and isolate expiration calculation in a helper.
- Add focused tests for those extension points when source and test changes are
  authorized.
- Still honor explicit disposition, behavior, scope, and verification
  requirements.
"""


def expected_variant(champion_text: str, block: str) -> str:
    if champion_text.count(INSERTION_ANCHOR) != 1:
        raise ValueError("locked variant insertion anchor is missing or ambiguous")
    return champion_text.replace(INSERTION_ANCHOR, INSERTION_ANCHOR + block)


def validate_locked_variants(variants: dict[str, Path]) -> None:
    champion = variants["champion"]
    if sha256_file(champion) != CHAMPION_SHA256:
        raise ValueError("champion hash does not match locked bytes")
    text = champion.read_text(encoding="utf-8")
    expected = {
        "karpathy-v1": expected_variant(text, CANDIDATE_BLOCK),
        "deliberately-bad": expected_variant(text, BAD_CONTROL_BLOCK),
    }
    for variant_id, expected_text in expected.items():
        path = variants.get(variant_id)
        if path is None:
            raise ValueError(f"locked variant is missing: {variant_id}")
        if path.read_text(encoding="utf-8") != expected_text:
            raise ValueError(f"{variant_id} differs from its single authorized block")
