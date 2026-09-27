#!/usr/bin/env python3
"""Calculate pre-adjudication agreement for the Pilot B blinded review."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KEY_PATH = ROOT / "results/pilot/pilot-b-reuse-blind-key.json"
PRIMARY_PATH = ROOT / "data/processed/pilot-b-reuse-review.json"
BASELINE_PATH = ROOT / "data/processed/pilot-a-reuse-full-review.json"
RESPONSES_PATH = ROOT / "results/pilot/pilot-b-reuse-reviewer2-responses.csv"
OUTPUT_PATH = ROOT / "results/pilot/pilot-b-reuse-review-agreement.json"
REUSE_LABELS = ("R0", "R1", "R2", "R3")
CONTEXT_LABELS = ("C0", "C1", "C2", "C3")


class AgreementError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AgreementError(f"Expected a JSON object in {path}")
    return value


def exact_agreement(first: list[str], second: list[str]) -> dict[str, Any]:
    if len(first) != len(second) or not first:
        raise AgreementError("Agreement requires equally sized non-empty lists")
    matches = sum(a == b for a, b in zip(first, second))
    return {"matches": matches, "n": len(first), "rate": matches / len(first)}


def weighted_kappa(first: list[str], second: list[str], labels: tuple[str, ...]) -> float | None:
    if len(first) != len(second) or not first:
        raise AgreementError("Kappa requires equally sized non-empty lists")
    index = {label: position for position, label in enumerate(labels)}
    try:
        first_indices = [index[label] for label in first]
        second_indices = [index[label] for label in second]
    except KeyError as exc:
        raise AgreementError(f"Unknown label: {exc.args[0]}") from exc
    denominator = max(len(labels) - 1, 1)
    observed = sum(abs(a - b) / denominator for a, b in zip(first_indices, second_indices)) / len(first)
    first_counts = Counter(first_indices)
    second_counts = Counter(second_indices)
    expected = sum(
        abs(a - b) / denominator
        * (first_counts[a] / len(first))
        * (second_counts[b] / len(second))
        for a in range(len(labels))
        for b in range(len(labels))
    )
    if expected == 0:
        return 1.0 if observed == 0 else None
    return 1.0 - observed / expected


def load_responses(path: Path, key: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    required = {
        "case_id", "variant", "reuse_class", "context_class", "candidate_symbol",
        "evidence", "maintenance_consequence", "confidence",
    }
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise AgreementError(f"Response CSV is missing columns: {sorted(missing)}")
        rows = list(reader)
    expected = {
        (case["case_id"], variant)
        for case in key["cases"]
        for variant in ("A", "B")
    }
    result: dict[tuple[str, str], dict[str, str]] = {}
    for raw in rows:
        row = {name: (value or "").strip() for name, value in raw.items()}
        identity = (row["case_id"], row["variant"].upper())
        if identity not in expected:
            raise AgreementError(f"Unexpected response row: {identity}")
        if identity in result:
            raise AgreementError(f"Duplicate response row: {identity}")
        if row["reuse_class"] not in REUSE_LABELS:
            raise AgreementError(f"{identity}: reuse_class must be R0-R3")
        if row["context_class"] not in CONTEXT_LABELS:
            raise AgreementError(f"{identity}: context_class must be C0-C3")
        for field in required - {"case_id", "variant"}:
            if not row[field]:
                raise AgreementError(f"{identity}: {field} is required")
        result[identity] = row
    if set(result) != expected:
        raise AgreementError(f"Missing response rows: {sorted(expected - set(result))}")
    return result


def calculate(responses_path: Path = RESPONSES_PATH) -> dict[str, Any]:
    key = read_json(KEY_PATH)
    responses = load_responses(responses_path, key)
    pilot_b = read_json(PRIMARY_PATH)
    baseline = read_json(BASELINE_PATH)
    pilot_b_index = {
        (row["condition"], row["task_slug"], int(row["turn"])): row
        for row in pilot_b["records"]
    }
    baseline_index = {
        (row["task_slug"], int(row["turn"])): row for row in baseline["records"]
    }

    comparisons = []
    for case in key["cases"]:
        for variant, field in (("A", "variant_a"), ("B", "variant_b")):
            origin = case[field]
            lookup = (case["task_slug"], int(case["turn"]))
            if origin["condition"] == "baseline":
                primary = baseline_index[lookup]
            else:
                primary = pilot_b_index[(origin["condition"], *lookup)]
            reviewer = responses[(case["case_id"], variant)]
            comparisons.append({
                "case_id": case["case_id"],
                "variant": variant,
                "condition": origin["condition"],
                "task_slug": case["task_slug"],
                "turn": int(case["turn"]),
                "primary_reuse_class": primary["reuse_class"],
                "second_reuse_class": reviewer["reuse_class"],
                "primary_context_class": primary["context_class"],
                "second_context_class": reviewer["context_class"],
                "reuse_agrees": primary["reuse_class"] == reviewer["reuse_class"],
                "context_agrees": primary["context_class"] == reviewer["context_class"],
                "second_reviewer_evidence": reviewer["evidence"],
            })

    first_reuse = [row["primary_reuse_class"] for row in comparisons]
    second_reuse = [row["second_reuse_class"] for row in comparisons]
    first_context = [row["primary_context_class"] for row in comparisons]
    second_context = [row["second_context_class"] for row in comparisons]
    first_binary = ["missed" if value in {"R2", "R3"} else "not-missed" for value in first_reuse]
    second_binary = ["missed" if value in {"R2", "R3"} else "not-missed" for value in second_reuse]
    return {
        "schema_version": 1,
        "status": "complete-pre-adjudication",
        "implementation_count": len(comparisons),
        "paired_case_count": len(key["cases"]),
        "reuse": {
            "exact_agreement": exact_agreement(first_reuse, second_reuse),
            "linear_weighted_cohens_kappa": weighted_kappa(first_reuse, second_reuse, REUSE_LABELS),
            "primary_counts": dict(sorted(Counter(first_reuse).items())),
            "second_reviewer_counts": dict(sorted(Counter(second_reuse).items())),
        },
        "binary_missed_reuse": {
            "definition": "R2 or R3",
            "exact_agreement": exact_agreement(first_binary, second_binary),
        },
        "context_availability": {
            "exact_agreement": exact_agreement(first_context, second_context),
            "linear_weighted_cohens_kappa": weighted_kappa(first_context, second_context, CONTEXT_LABELS),
            "primary_counts": dict(sorted(Counter(first_context).items())),
            "second_reviewer_counts": dict(sorted(Counter(second_context).items())),
        },
        "cases": comparisons,
        "disagreements": [
            row for row in comparisons
            if not row["reuse_agrees"] or not row["context_agrees"]
        ],
        "interpretation_note": (
            "Descriptive reliability evidence for a purposive 20-implementation sample. "
            "Trajectory turns are dependent observations; report pre-adjudication agreement separately from final consensus labels."
        ),
    }


def main() -> int:
    result = calculate()
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "reuse": result["reuse"],
        "binary_missed_reuse": result["binary_missed_reuse"],
        "context_availability": result["context_availability"],
        "disagreements": result["disagreements"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
