#!/usr/bin/env python3
"""Validate and summarize the Pilot B reuse review."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiment/config/pilot-b.json"
FUNCTIONAL_PATH = ROOT / "results/pilot/pilot-b-functional-summary.json"
REVIEW_PATH = ROOT / "data/processed/pilot-b-reuse-review.json"
BASELINE_REVIEW_PATH = ROOT / "data/processed/pilot-a-reuse-full-review.json"
CSV_PATH = ROOT / "data/processed/pilot-b-reuse-review.csv"
SUMMARY_PATH = ROOT / "results/pilot/pilot-b-reuse-summary.json"

NEW_CONDITIONS = (
    "engineering-guardrails",
    "engineering-guardrails-retrieval",
)
REUSE_LABELS = {"R0", "R1", "R2", "R3"}
CONTEXT_LABELS = {"C0", "C1", "C2", "C3"}
REFERENCE_INELIGIBLE = {
    "loadDocuments": {2, 3},
    "nodeArrayMerge": {5},
    "randomAccessScoreProvider": {4},
}
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
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReviewError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def artifact_digest(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def identity(row: dict[str, Any]) -> tuple[str, int]:
    return str(row["task_slug"]), int(row["turn"])


def review_identity(row: dict[str, Any]) -> tuple[str, str, int]:
    return str(row["condition"]), str(row["task_slug"]), int(row["turn"])


def find_record(run_id: str) -> Path:
    matches = list((ROOT / "data/generated-trajectories").glob(f"**/{run_id}/record.json"))
    if len(matches) != 1:
        raise ReviewError(f"Expected one record for {run_id}, found {len(matches)}")
    return matches[0]


def expected_new_checkpoints(
    config: dict[str, Any],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    expected: dict[tuple[str, str, int], dict[str, Any]] = {}
    for condition in NEW_CONDITIONS:
        for task in config["tasks"]:
            run_id = f"{config['batch_id']}-{condition}-{task['slug']}-01"
            record = read_json(find_record(run_id))
            for turn in record["turns"]:
                turn_number = int(turn["turn"])
                if not turn.get("cumulatively_correct"):
                    continue
                if turn_number in REFERENCE_INELIGIBLE.get(task["slug"], set()):
                    continue
                key = (condition, task["slug"], turn_number)
                expected[key] = {
                    "run_id": run_id,
                    "repository": task["repo"],
                    "generated_code_sha256": hashlib.sha256(
                        turn["extracted_code"].encode("utf-8")
                    ).hexdigest(),
                }
    if len(expected) != 23:
        raise ReviewError(
            f"Expected 23 new eligible correct checkpoints, found {len(expected)}"
        )
    return expected


def validate_review(
    review: dict[str, Any], expected: dict[tuple[str, str, int], dict[str, Any]]
) -> list[dict[str, Any]]:
    records = review.get("records")
    if not isinstance(records, list):
        raise ReviewError("Review records must be an array")
    actual: set[tuple[str, str, int]] = set()
    for row in records:
        key = review_identity(row)
        if key in actual:
            raise ReviewError(f"Duplicate checkpoint {key}")
        actual.add(key)
        if row.get("reuse_class") not in REUSE_LABELS:
            raise ReviewError(f"{key}: invalid reuse class")
        if row.get("context_class") not in CONTEXT_LABELS:
            raise ReviewError(f"{key}: invalid context class")
        missing = sorted(
            name for name in REQUIRED_TEXT if not str(row.get(name, "")).strip()
        )
        if missing:
            raise ReviewError(f"{key}: missing fields {missing}")
        expected_row = expected.get(key)
        if expected_row is None:
            raise ReviewError(f"Unexpected reviewed checkpoint {key}")
        if row.get("run_id") != expected_row["run_id"]:
            raise ReviewError(f"{key}: run ID mismatch")
        if row.get("repository") != expected_row["repository"]:
            raise ReviewError(f"{key}: repository mismatch")
    if actual != set(expected):
        raise ReviewError(
            f"Checkpoint mismatch; missing={sorted(set(expected) - actual)}, "
            f"extra={sorted(actual - set(expected))}"
        )
    return records


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reuse = Counter(row["reuse_class"] for row in rows)
    context = Counter(row["context_class"] for row in rows)
    missed = [row for row in rows if row["reuse_class"] in {"R2", "R3"}]
    trajectories = {row["task_slug"] for row in rows}
    missed_trajectories = {row["task_slug"] for row in missed}
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[row["task_slug"]].append(row)
    return {
        "checkpoints": len(rows),
        "trajectories": len(trajectories),
        "reuse_class_counts": {
            label: reuse.get(label, 0) for label in sorted(REUSE_LABELS)
        },
        "context_class_counts": {
            label: context.get(label, 0) for label in sorted(CONTEXT_LABELS)
        },
        "missed_reuse": {
            "definition": "R2 or R3",
            "checkpoints": len(missed),
            "trajectories": len(missed_trajectories),
            "by_context": {
                label: sum(row["context_class"] == label for row in missed)
                for label in sorted(CONTEXT_LABELS)
            },
        },
        "tasks": [
            {
                "task_slug": task_slug,
                "turns": [
                    int(row["turn"])
                    for row in sorted(task_rows, key=lambda item: int(item["turn"]))
                ],
                "reuse_sequence": [
                    row["reuse_class"]
                    for row in sorted(task_rows, key=lambda item: int(item["turn"]))
                ],
                "context_sequence": [
                    row["context_class"]
                    for row in sorted(task_rows, key=lambda item: int(item["turn"]))
                ],
            }
            for task_slug, task_rows in sorted(by_task.items())
        ],
    }


def transition_summary(
    before_rows: list[dict[str, Any]], after_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    before = {identity(row): row for row in before_rows}
    after = {identity(row): row for row in after_rows}
    shared = sorted(set(before) & set(after))
    reuse_transitions = Counter(
        f"{before[key]['reuse_class']}->{after[key]['reuse_class']}" for key in shared
    )
    context_transitions = Counter(
        f"{before[key]['context_class']}->{after[key]['context_class']}" for key in shared
    )
    improved = [
        {
            "task_slug": key[0],
            "turn": key[1],
            "transition": f"{before[key]['reuse_class']}->{after[key]['reuse_class']}",
        }
        for key in shared
        if before[key]["reuse_class"] in {"R2", "R3"}
        and after[key]["reuse_class"] in {"R0", "R1"}
    ]
    regressed = [
        {
            "task_slug": key[0],
            "turn": key[1],
            "transition": f"{before[key]['reuse_class']}->{after[key]['reuse_class']}",
        }
        for key in shared
        if before[key]["reuse_class"] in {"R0", "R1"}
        and after[key]["reuse_class"] in {"R2", "R3"}
    ]
    return {
        "shared_functionally_correct_checkpoints": len(shared),
        "reuse_transitions": dict(sorted(reuse_transitions.items())),
        "context_transitions": dict(sorted(context_transitions.items())),
        "missed_to_appropriate": improved,
        "appropriate_to_missed": regressed,
        "newly_functionally_correct_after": [
            {
                "task_slug": key[0],
                "turn": key[1],
                "reuse_class": after[key]["reuse_class"],
            }
            for key in sorted(set(after) - set(before))
        ],
        "lost_functional_correctness_after": [
            {
                "task_slug": key[0],
                "turn": key[1],
                "reuse_class": before[key]["reuse_class"],
            }
            for key in sorted(set(before) - set(after))
        ],
    }


def baseline_rows(
    config: dict[str, Any], baseline_review: dict[str, Any]
) -> list[dict[str, Any]]:
    task_slugs = {task["slug"] for task in config["tasks"]}
    rows = [
        dict(row, condition="baseline")
        for row in baseline_review["records"]
        if row["task_slug"] in task_slugs
    ]
    if len(rows) != 10:
        raise ReviewError(f"Expected 10 reviewed baseline checkpoints, found {len(rows)}")
    return rows


def build_outputs() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    config = read_json(CONFIG_PATH)
    functional = read_json(FUNCTIONAL_PATH)
    review = read_json(REVIEW_PATH)
    baseline_review = read_json(BASELINE_REVIEW_PATH)
    expected = expected_new_checkpoints(config)
    records = validate_review(review, expected)
    by_condition = {
        condition: [row for row in records if row["condition"] == condition]
        for condition in NEW_CONDITIONS
    }
    baseline = baseline_rows(config, baseline_review)
    guardrails = by_condition["engineering-guardrails"]
    retrieval = by_condition["engineering-guardrails-retrieval"]

    condition_summaries = {
        "baseline": summarize_rows(baseline),
        "engineering-guardrails": summarize_rows(guardrails),
        "engineering-guardrails-retrieval": summarize_rows(retrieval),
    }
    if condition_summaries["engineering-guardrails"]["checkpoints"] != 9:
        raise ReviewError("Expected nine guardrails-only reviewed checkpoints")
    if condition_summaries["engineering-guardrails-retrieval"]["checkpoints"] != 14:
        raise ReviewError("Expected fourteen retrieval reviewed checkpoints")

    source_paths = [
        CONFIG_PATH,
        FUNCTIONAL_PATH,
        REVIEW_PATH,
        BASELINE_REVIEW_PATH,
        *sorted((ROOT / "experiment/pilot-b/retrieval").glob("*.txt")),
        *sorted((ROOT / "data/generated-trajectories/pilot-b").glob("*/record.json")),
    ]
    summary = {
        "schema_version": 1,
        "status": "complete-primary-review",
        "batch_id": config["batch_id"],
        "unit": review["unit"],
        "review_reliability": {
            "pilot_a_calibration": "R0-R3 exact agreement 9/10; binary missed-reuse agreement 10/10; weighted kappa 0.889.",
            "pilot_b_status": review["review_limitations"],
        },
        "conditions": condition_summaries,
        "paired_comparisons": {
            "guardrails_vs_baseline": transition_summary(baseline, guardrails),
            "retrieval_vs_guardrails": transition_summary(guardrails, retrieval),
            "retrieval_vs_baseline": transition_summary(baseline, retrieval),
        },
        "incorrect_task_diagnosis": review["incorrect_task_diagnosis"],
        "interpretation": {
            "guardrails_only": "Guardrails alone preserve the four baseline-like nodeArrayMerge missed-reuse checkpoints; advice without API exposure does not change the reuse path.",
            "retrieval": "All 14 retrieval-supported eligible correct checkpoints are R1. On the nine checkpoints correct in both new conditions, four nodeArrayMerge checkpoints change from R2/C1 to R1/C3 and five remain R1.",
            "boundary": "The task packets were selected after Pilot A, there is one run per task and condition, checkpoints are dependent, and the Pilot B primary reviewer knew the condition. Treat this as targeted mechanism evidence, not a population-level causal estimate.",
        },
        "source_artifacts": [artifact_digest(path) for path in source_paths],
        "functional_summary_sha256": hashlib.sha256(
            FUNCTIONAL_PATH.read_bytes()
        ).hexdigest(),
        "functional_batch_id": functional["batch_id"],
    }

    csv_rows = []
    for row in records:
        expected_row = expected[review_identity(row)]
        csv_rows.append(
            {
                **row,
                "missed_reuse": str(
                    row["reuse_class"] in {"R2", "R3"}
                ).lower(),
                "generated_code_sha256": expected_row["generated_code_sha256"],
            }
        )
    return summary, csv_rows


def write_outputs(summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    write_json(SUMMARY_PATH, summary)
    fields = [
        "condition",
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
        "generated_code_sha256",
    ]
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, "") for field in fields} for row in rows
        )


def main() -> int:
    try:
        summary, rows = build_outputs()
        write_outputs(summary, rows)
        print(json.dumps(summary["conditions"], indent=2))
        print(json.dumps(summary["paired_comparisons"], indent=2))
        print(f"Report: {SUMMARY_PATH}")
        return 0
    except (ReviewError, KeyError, TypeError, ZeroDivisionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
