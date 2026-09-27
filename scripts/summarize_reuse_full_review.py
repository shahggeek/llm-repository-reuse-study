#!/usr/bin/env python3
"""Validate and summarize the complete Pilot A reuse review."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "data/processed/pilot-a-reuse-full-review.json"
CANDIDATE_PATH = ROOT / "data/processed/pilot-a-reuse-candidates.json"
STRUCTURAL_PATH = ROOT / "data/processed/pilot-a-structural-metrics.json"
CSV_PATH = ROOT / "data/processed/pilot-a-reuse-full-review.csv"
SUMMARY_PATH = ROOT / "results/pilot/pilot-a-reuse-full-review-summary.json"
REUSE_LABELS = {"R0", "R1", "R2", "R3"}
CONTEXT_LABELS = {"C0", "C1", "C2", "C3"}
REQUIRED_TEXT = {
    "candidate_symbol",
    "evidence",
    "context_evidence",
    "maintenance_consequence",
    "confidence",
    "review_source",
}


class ReviewError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["task_slug"]), int(row["turn"])


def validate(review: dict[str, Any], candidates: dict[str, Any]) -> list[dict[str, Any]]:
    records = review.get("records")
    if not isinstance(records, list):
        raise ReviewError("Review records must be an array")

    expected = {identity(row) for row in candidates["records"]}
    actual: set[tuple[str, int]] = set()
    for row in records:
        key = identity(row)
        if key in actual:
            raise ReviewError(f"Duplicate checkpoint: {key}")
        actual.add(key)
        if row.get("reuse_class") not in REUSE_LABELS:
            raise ReviewError(f"{key}: invalid reuse_class")
        if row.get("context_class") not in CONTEXT_LABELS:
            raise ReviewError(f"{key}: invalid context_class")
        missing = sorted(name for name in REQUIRED_TEXT if not str(row.get(name, "")).strip())
        if missing:
            raise ReviewError(f"{key}: missing fields {missing}")
    if actual != expected:
        raise ReviewError(f"Checkpoint mismatch; missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    return records


def build_outputs() -> dict[str, Any]:
    review = read_json(REVIEW_PATH)
    candidates = read_json(CANDIDATE_PATH)
    structural = read_json(STRUCTURAL_PATH)
    records = validate(review, candidates)
    candidate_index = {identity(row): row for row in candidates["records"]}
    structural_index = {identity(row): row for row in structural["records"]}

    csv_fields = [
        "task_slug",
        "repository",
        "turn",
        "run_id",
        "reuse_class",
        "context_class",
        "missed_reuse",
        "candidate_symbol",
        "evidence",
        "context_evidence",
        "maintenance_consequence",
        "confidence",
        "review_source",
        "screen_priority",
        "screen_flagged",
        "reference_only_calls",
        "generated_only_calls",
        "generated_code_sha256",
        "reference_code_sha256",
    ]
    csv_rows = []
    for row in records:
        key = identity(row)
        candidate = candidate_index[key]
        metrics = structural_index[key]
        missed = row["reuse_class"] in {"R2", "R3"}
        csv_rows.append(
            {
                **{name: row.get(name, "") for name in csv_fields},
                "missed_reuse": str(missed).lower(),
                "screen_priority": candidate["screen_priority"],
                "screen_flagged": str(bool(candidate["requires_manual_review"])).lower(),
                "reference_only_calls": ";".join(candidate["reference_only_calls"]),
                "generated_only_calls": ";".join(candidate["generated_only_calls"]),
                "generated_code_sha256": metrics["generated_code_sha256"],
                "reference_code_sha256": metrics["reference_code_sha256"],
            }
        )

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(csv_rows)

    reuse_counts = Counter(row["reuse_class"] for row in records)
    context_counts = Counter(row["context_class"] for row in records)
    missed = [row for row in records if row["reuse_class"] in {"R2", "R3"}]
    trajectories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        trajectories[row["task_slug"]].append(row)
    for rows in trajectories.values():
        rows.sort(key=lambda item: int(item["turn"]))

    trajectory_rows = []
    for task_slug in sorted(trajectories):
        rows = trajectories[task_slug]
        missed_rows = [row for row in rows if row["reuse_class"] in {"R2", "R3"}]
        trajectory_rows.append(
            {
                "task_slug": task_slug,
                "checkpoint_count": len(rows),
                "class_sequence": [row["reuse_class"] for row in rows],
                "context_sequence": [row["context_class"] for row in rows],
                "missed_reuse_checkpoints": len(missed_rows),
                "first_missed_reuse_turn": min((int(row["turn"]) for row in missed_rows), default=None),
            }
        )

    true_positive = sum(
        row["reuse_class"] in {"R2", "R3"} and candidate_index[identity(row)]["requires_manual_review"]
        for row in records
    )
    false_positive = sum(
        row["reuse_class"] not in {"R2", "R3"} and candidate_index[identity(row)]["requires_manual_review"]
        for row in records
    )
    true_negative = sum(
        row["reuse_class"] not in {"R2", "R3"} and not candidate_index[identity(row)]["requires_manual_review"]
        for row in records
    )
    false_negative = sum(
        row["reuse_class"] in {"R2", "R3"} and not candidate_index[identity(row)]["requires_manual_review"]
        for row in records
    )

    summary = {
        "schema_version": 1,
        "status": "complete-manual-review",
        "unit": review["unit"],
        "context_basis": review["context_basis"],
        "sample": {
            "checkpoints": len(records),
            "trajectories": len(trajectories),
            "repositories": len({row["repository"] for row in records}),
        },
        "reuse_class_counts": {label: reuse_counts.get(label, 0) for label in sorted(REUSE_LABELS)},
        "context_class_counts": {label: context_counts.get(label, 0) for label in sorted(CONTEXT_LABELS)},
        "missed_reuse": {
            "definition": "R2 or R3",
            "checkpoints": len(missed),
            "checkpoint_rate": len(missed) / len(records),
            "trajectories": sum(row["missed_reuse_checkpoints"] > 0 for row in trajectory_rows),
            "trajectory_rate": sum(row["missed_reuse_checkpoints"] > 0 for row in trajectory_rows) / len(trajectory_rows),
            "by_context": {
                label: sum(row["context_class"] == label for row in missed)
                for label in sorted(CONTEXT_LABELS)
            },
        },
        "screen_performance_on_reviewed_pool": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
            "precision": true_positive / (true_positive + false_positive),
            "recall": true_positive / (true_positive + false_negative),
            "interpretation": "Descriptive triage performance on the purposive eligible Pilot A pool; not an external validation estimate.",
        },
        "trajectories": trajectory_rows,
        "prompt_provenance_correction": {
            "task_slug": "ensureCapacity",
            "turn": 2,
            "prior_context_class": "C2",
            "corrected_context_class": "C3",
            "reason": "The exact turn-2 prompt explicitly included ArrayUtil.grow() in the previous generated method. The blinded review packet exposed only the initial context slice.",
            "reuse_class_changed": False,
            "missed_reuse_changed": False,
        },
        "cross_pilot_consistency_correction": {
            "artifact": "results/pilot/pilot-a-reuse-consistency-correction.json",
            "task_slug": "nodeArrayMerge",
            "turn": 1,
            "prior_reuse_class": "R2",
            "corrected_reuse_class": "R3",
            "reason": "System.arraycopy() is a low-level copy mechanism, not partial reuse of NodeArray.addInOrder().",
            "binary_missed_reuse_changed": False,
            "context_class_changed": False,
        },
        "interpretation": "Eleven checkpoint observations contain repository-level missed reuse, but they are repeated states within four trajectories. Six are C1 and five are C2; none occurs with the applicable helper explicit in the model context. Report checkpoint and trajectory units together and do not treat checkpoints as independent.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    summary = build_outputs()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
