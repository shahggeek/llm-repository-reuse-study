#!/usr/bin/env python3
"""Validate the manual prompt-context sufficiency audit against frozen packets."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "experiment/config/pilot-tasks.json"
AMENDMENT_PATH = ROOT / "experiment/config/pilot-a-amendment.json"
AUDIT_PATH = ROOT / "results/pilot/prompt-context-sufficiency-audit.json"
PACKET_DIR = ROOT / "work/task-packets"
AMENDMENT_PACKET_DIR = ROOT / "work/amendment-task-packets"
ALLOWED_CLASSIFICATIONS = {
    "explicit-consistent",
    "inferable-consistent",
    "partially-conflicting",
    "underspecified-integration-types",
}


class AuditError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"Expected a JSON object in {path}")
    return value


def adjusted_tasks(
    manifest: dict[str, Any], amendment: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    replaced = {row["replaces"]["slug"] for row in amendment["replacements"]}
    tasks = {task["slug"]: task for task in manifest["tasks"] if task["slug"] not in replaced}
    tasks.update({row["task"]["slug"]: row["task"] for row in amendment["replacements"]})
    return tasks


def packet_path(slug: str) -> Path:
    amendment_path = AMENDMENT_PACKET_DIR / f"{slug}.json"
    return amendment_path if amendment_path.is_file() else PACKET_DIR / f"{slug}.json"


def validate_audit(
    manifest: dict[str, Any], amendment: dict[str, Any], audit: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    expected = adjusted_tasks(manifest, amendment)
    rows = audit.get("tasks")
    if not isinstance(rows, list):
        return ["audit tasks must be an array"]
    actual = {row.get("slug"): row for row in rows if isinstance(row, dict)}
    if set(actual) != set(expected):
        errors.append("audit task coverage differs from adjusted Pilot A")
    if len(rows) != len(actual):
        errors.append("audit contains duplicate or malformed task rows")

    counts = {classification: 0 for classification in ALLOWED_CLASSIFICATIONS}
    sensitivity_checkpoints = 0
    strict_tasks = 0
    strict_checkpoints = 0
    for slug, task in expected.items():
        row = actual.get(slug)
        if row is None:
            continue
        if row.get("hash_id") != task["hash_id"]:
            errors.append(f"{slug}: hash mismatch")
        classification = row.get("classification")
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"{slug}: invalid classification {classification!r}")
        else:
            counts[classification] += 1
        turns = row.get("affected_turns")
        if not isinstance(turns, list) or any(
            not isinstance(turn, int) or turn < 1 or turn > task["turns"] for turn in turns
        ):
            errors.append(f"{slug}: invalid affected_turns")
            continue
        packet = read_json(packet_path(slug))
        if packet.get("study_task", {}).get("hash_id") != task["hash_id"]:
            errors.append(f"{slug}: packet hash mismatch")
        if len(packet.get("turn_datas", [])) != task["turns"]:
            errors.append(f"{slug}: packet turn count mismatch")
        if row.get("analysis_action") == "retain-frozen-primary-exclude-context-sensitivity":
            sensitivity_checkpoints += len(turns)
        if classification in {"inferable-consistent", "underspecified-integration-types"}:
            strict_tasks += 1
            strict_checkpoints += task["turns"]

    expected_counts = {
        "explicit-consistent": audit["summary"]["explicit_consistent"],
        "inferable-consistent": audit["summary"]["inferable_consistent"],
        "partially-conflicting": audit["summary"]["partially_conflicting"],
        "underspecified-integration-types": audit["summary"][
            "underspecified_integration_types"
        ],
    }
    if counts != expected_counts:
        errors.append(f"classification summary mismatch: {counts} != {expected_counts}")
    if sensitivity_checkpoints != audit["summary"]["new_sensitivity_excluded_checkpoints"]:
        errors.append("sensitivity checkpoint count mismatch")
    if strict_tasks != audit["summary"]["strict_explicit_signature_excluded_tasks"]:
        errors.append("strict sensitivity task count mismatch")
    if strict_checkpoints != audit["summary"]["strict_explicit_signature_excluded_checkpoints"]:
        errors.append("strict sensitivity checkpoint count mismatch")

    rerank = read_json(packet_path("rerank"))
    supplied = rerank["metadata"]["context"] + rerank["turn_datas"][0]["instruction"]
    for hidden_type in ("ScoreFunction.ExactScoreFunction", "NodesUnsorted"):
        if hidden_type in supplied:
            errors.append(f"rerank: {hidden_type} is unexpectedly present in supplied prompt material")
    set_packet = read_json(packet_path("set"))
    set_instruction = set_packet["turn_datas"][0]["instruction"]
    set_reference = set_packet["turn_datas"][0]["solution"]
    if "BooleanSupplier" in set_instruction or "BooleanSupplier" not in set_reference:
        errors.append("set: expected turn-1 signature conflict is not present")
    return errors


def main() -> int:
    try:
        manifest = read_json(MANIFEST_PATH)
        amendment = read_json(AMENDMENT_PATH)
        audit = read_json(AUDIT_PATH)
        errors = validate_audit(manifest, amendment, audit)
        if errors:
            raise AuditError("Invalid audit:\n- " + "\n- ".join(errors))
        print(
            "Prompt-context audit valid: 18 tasks; "
            "13 explicit, 3 inferable, 1 partial conflict, 1 underspecified"
        )
        return 0
    except (AuditError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
