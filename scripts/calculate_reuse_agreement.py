#!/usr/bin/env python3
"""Calculate independent-review agreement for the Pilot A reuse rubric."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KEY_PATH = ROOT / "results/pilot/pilot-a-reuse-blind-key.json"
PRIMARY_PATH = ROOT / "results/pilot/pilot-a-reuse-rubric-pilot.json"
REUSE_LABELS = ("R0", "R1", "R2", "R3")
CONTEXT_LABELS = ("C0", "C1", "C2", "C3")


class AgreementError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def weighted_kappa(first: list[str], second: list[str], labels: tuple[str, ...]) -> float | None:
    if len(first) != len(second) or not first:
        raise AgreementError("Kappa requires equally sized non-empty label lists")
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
    expected = 0.0
    for a in range(len(labels)):
        for b in range(len(labels)):
            weight = abs(a - b) / denominator
            expected += weight * (first_counts[a] / len(first)) * (second_counts[b] / len(second))
    if expected == 0:
        return 1.0 if observed == 0 else None
    return 1.0 - observed / expected


def exact_agreement(first: list[str], second: list[str]) -> dict[str, Any]:
    matches = sum(a == b for a, b in zip(first, second))
    return {"matches": matches, "n": len(first), "rate": matches / len(first)}


def load_responses(path: Path, key: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    required = {
        "case_id",
        "variant",
        "reuse_class",
        "context_class",
        "candidate_symbol",
        "evidence",
        "maintenance_consequence",
        "confidence",
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
    for row in rows:
        identity = (row["case_id"].strip(), row["variant"].strip().upper())
        if identity not in expected:
            continue
        if identity in result:
            raise AgreementError(f"Duplicate response row: {identity}")
        normalized = {name: (value or "").strip() for name, value in row.items()}
        if normalized["reuse_class"] not in REUSE_LABELS:
            raise AgreementError(f"{identity}: reuse_class must be R0-R3")
        if normalized["context_class"] not in CONTEXT_LABELS:
            raise AgreementError(f"{identity}: context_class must be C0-C3")
        if not normalized["evidence"]:
            raise AgreementError(f"{identity}: evidence is required")
        result[identity] = normalized
    missing_rows = expected - set(result)
    if missing_rows:
        raise AgreementError(f"Complete both variants for every case; missing {sorted(missing_rows)}")
    return result


def calculate(responses: dict[tuple[str, str], dict[str, str]]) -> dict[str, Any]:
    key = read_json(KEY_PATH)
    primary = read_json(PRIMARY_PATH)
    primary_index = {
        (row["task_slug"], int(row["turn"])): row
        for row in primary["classifications"]
    }
    cases = []
    for case in key["cases"]:
        primary_row = primary_index[(case["task_slug"], int(case["turn"]))]
        second = responses[(case["case_id"], case["generated_variant"])]
        cases.append(
            {
                "case_id": case["case_id"],
                "task_slug": case["task_slug"],
                "turn": case["turn"],
                "primary_reuse_class": primary_row["reuse_class"],
                "second_reuse_class": second["reuse_class"],
                "primary_context_class": primary_row["context_class"],
                "second_context_class": second["context_class"],
                "reuse_agrees": primary_row["reuse_class"] == second["reuse_class"],
                "context_agrees": primary_row["context_class"] == second["context_class"],
                "second_reviewer_evidence": second["evidence"],
            }
        )

    first_reuse = [row["primary_reuse_class"] for row in cases]
    second_reuse = [row["second_reuse_class"] for row in cases]
    first_context = [row["primary_context_class"] for row in cases]
    second_context = [row["second_context_class"] for row in cases]
    first_binary = ["missed" if value in {"R2", "R3"} else "not-missed" for value in first_reuse]
    second_binary = ["missed" if value in {"R2", "R3"} else "not-missed" for value in second_reuse]
    return {
        "schema_version": 1,
        "sample_size": len(cases),
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
        "cases": cases,
        "interpretation_note": "Descriptive calibration result for ten generated checkpoints; inspect case disagreements before expanding the rubric review.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("responses", type=Path, help="CSV exported from the completed Review sheet")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    key = read_json(KEY_PATH)
    responses = load_responses(args.responses, key)
    result = calculate(responses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
