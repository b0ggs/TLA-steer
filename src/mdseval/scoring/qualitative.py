"""Blinded pairwise judge packet construction and strict output parsing."""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any

from ..config import ConfigError

WINNERS = frozenset({"A", "B", "TIE"})
CONFIDENCES = frozenset({"low", "medium", "high"})
DIMENSIONS = (
    "assumption_handling",
    "simplicity",
    "scope_discipline",
    "verification_quality",
)

JUDGE_INSTRUCTIONS = """Compare Response A and Response B using only the blinded packet.
Mechanical hard failures are already measured; do not reinterpret them.
Assess assumption handling, simplicity proportional to the contract, scope
discipline, and verification quality. Prefer TIE when differences are not
meaningful. Do not reward verbosity, extra files, extra abstractions, or larger
diffs by themselves. Cite concrete packet evidence. Return only JSON matching
judge-output.schema.json.
"""

INSTRUCTION_TOKEN = re.compile(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*")


def randomize_labels(seed: int, case_id: str, replicate: int) -> dict[str, str]:
    rng = random.Random(f"{seed}:{case_id}:{replicate}")
    if rng.randrange(2):
        return {"A": "left", "B": "right"}
    return {"A": "right", "B": "left"}


def _original_files(fixture: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(fixture.rglob("*")):
        if path.is_file() and not path.is_symlink():
            relative = path.relative_to(fixture).as_posix()
            with path.open("rb") as stream:
                data = stream.read(32_769)
            if len(data) <= 32_768:
                try:
                    result[relative] = data.decode("utf-8")
                except UnicodeDecodeError:
                    result[relative] = "[binary file omitted]"
    return result


def _blind_diff(diff: str) -> str:
    sections = diff.split("diff --git ")
    kept: list[str] = []
    for section in sections:
        if not section:
            continue
        header = section.splitlines()[0] if section.splitlines() else ""
        if "CODER.md" in header or ".issue-contract.md" in header:
            kept.append("[forbidden instruction/contract change omitted]\n")
        else:
            kept.append("diff --git " + section)
    return "".join(kept)


def _token_ngrams(texts: tuple[str, ...]) -> set[tuple[str, ...]]:
    ngrams: set[tuple[str, ...]] = set()
    for text in texts:
        tokens = INSTRUCTION_TOKEN.findall(text.lower())
        for size in (2, 3, 4, 5):
            for index in range(max(0, len(tokens) - size + 1)):
                fragment = tuple(tokens[index : index + size])
                if len(" ".join(fragment)) >= 16:
                    ngrams.add(fragment)
    return ngrams


def _contains_instruction_fragment(
    value: str, instruction_ngrams: set[tuple[str, ...]]
) -> bool:
    tokens = INSTRUCTION_TOKEN.findall(value.lower())
    return any(
        tuple(tokens[index : index + size]) in instruction_ngrams
        for size in (2, 3, 4, 5)
        for index in range(max(0, len(tokens) - size + 1))
    )


def _sanitize(
    value: Any,
    forbidden_strings: tuple[str, ...],
    instruction_ngrams: set[tuple[str, ...]],
) -> Any:
    if isinstance(value, str):
        for forbidden in sorted(
            (item for item in forbidden_strings if item), key=len, reverse=True
        ):
            value = re.sub(
                re.escape(forbidden), "[BLINDED]", value, flags=re.IGNORECASE
            )
        if _contains_instruction_fragment(value, instruction_ngrams):
            return "[BLINDED INSTRUCTION-DERIVED CONTENT]"
        return value
    if isinstance(value, list):
        return [_sanitize(item, forbidden_strings, instruction_ngrams) for item in value]
    if isinstance(value, dict):
        return {
            key: _sanitize(item, forbidden_strings, instruction_ngrams)
            for key, item in value.items()
            if key not in {"variant_id", "variant_hash", "evidence_path"}
        }
    return value


def _instruction_fragments(text: str) -> tuple[str, ...]:
    fragments: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        normalized = stripped.lstrip("-*# 0123456789.").strip()
        if len(stripped) >= 16:
            fragments.append(stripped)
        if len(normalized) >= 16:
            fragments.append(normalized)
    return tuple(fragments)


def build_blinded_packet(
    *,
    case_id: str,
    replicate: int,
    seed: int,
    contract: str,
    fixture: Path,
    left: dict[str, Any],
    right: dict[str, Any],
    variant_ids: tuple[str, str],
    variant_paths: tuple[str, str],
    instruction_texts: tuple[str, str],
) -> tuple[dict[str, Any], dict[str, str]]:
    labels = randomize_labels(seed, case_id, replicate)
    responses = {"left": left, "right": right}
    packet_responses: dict[str, Any] = {}
    forbidden = (
        *variant_ids,
        *variant_paths,
        *(Path(path).name for path in variant_paths),
        *instruction_texts,
        *(fragment for text in instruction_texts for fragment in _instruction_fragments(text)),
    )
    for label, side in labels.items():
        response = responses[side]
        packet_responses[label] = {
            "final_response": response.get("final_text", ""),
            "diff": _blind_diff(str(response.get("diff", ""))),
            "commands": response.get("commands", []),
            "mechanical_checks": response.get("mechanical", {}).get("fields", {}),
            "usage": response.get("usage", {}),
            "duration_seconds": response.get("duration_seconds"),
        }
    # Apply short-phrase instruction blinding only to subject responses. The
    # contract and fixture are authoritative judge context and may naturally
    # share ordinary three-word phrases with CODER.md.
    packet_responses = _sanitize(
        packet_responses, forbidden, _token_ngrams(instruction_texts)
    )
    packet = {
        "schema_version": 1,
        "case_id": case_id,
        "replicate": replicate,
        "contract": contract,
        "original_fixture_files": _original_files(fixture),
        "responses": packet_responses,
        "judge_instructions": JUDGE_INSTRUCTIONS,
    }
    packet = _sanitize(packet, forbidden, set())
    serialized = json.dumps(packet, sort_keys=True)
    leaks = [item for item in forbidden if item and item in serialized]
    if leaks:
        raise ValueError("judge packet contains variant identity or instruction content")
    return packet, labels


def parse_judge_output(value: str | dict[str, Any]) -> dict[str, Any]:
    try:
        data = json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid judge JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("judge output must be an object")
    required = {"schema_version", "winner", "confidence", "dimensions", "hard_concerns"}
    if set(data) != required:
        raise ConfigError(f"judge output keys must be exactly {sorted(required)}")
    if data["schema_version"] != 1 or data["winner"] not in WINNERS:
        raise ConfigError("invalid judge schema version or winner")
    if data["confidence"] not in CONFIDENCES:
        raise ConfigError("invalid judge confidence")
    dimensions = data["dimensions"]
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        raise ConfigError("judge dimensions are incomplete or unknown")
    for name, result in dimensions.items():
        if (
            not isinstance(result, dict)
            or set(result) != {"winner", "reason"}
            or result["winner"] not in WINNERS
            or not isinstance(result["reason"], str)
            or not result["reason"].strip()
        ):
            raise ConfigError(f"invalid judge dimension {name}")
    concerns = data["hard_concerns"]
    if not isinstance(concerns, list) or not all(isinstance(item, str) for item in concerns):
        raise ConfigError("hard_concerns must be a string list")
    return data


def restore_winner(winner: str, labels: dict[str, str]) -> str:
    return "TIE" if winner == "TIE" else labels[winner]
