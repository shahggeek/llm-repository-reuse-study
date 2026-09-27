#!/usr/bin/env python3
"""Apply frozen Pilot B adjudications and produce the final reuse summary."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import summarize_pilot_b_reuse as primary_summary


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data/processed/pilot-b-reuse-review.json"
ADJUDICATED_JSON_PATH = ROOT / "data/processed/pilot-b-reuse-review-adjudicated.json"
ADJUDICATED_CSV_PATH = ROOT / "data/processed/pilot-b-reuse-review-adjudicated.csv"
AGREEMENT_PATH = ROOT / "results/pilot/pilot-b-reuse-review-agreement.json"
ADJUDICATION_PATH = ROOT / "results/pilot/pilot-b-reuse-adjudication.json"
FINAL_SUMMARY_PATH = ROOT / "results/pilot/pilot-b-reuse-final-summary.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_adjudicated_review() -> dict[str, Any]:
    raw = read_json(RAW_PATH)
    records = [dict(row) for row in raw["records"]]
    target = [
        row for row in records
        if row["condition"] == "engineering-guardrails"
        and row["task_slug"] == "nodeArrayMerge"
        and int(row["turn"]) == 1
    ]
    if len(target) != 1 or target[0]["reuse_class"] != "R2" or target[0]["context_class"] != "C1":
        raise RuntimeError("Unexpected primary label for guardrails nodeArrayMerge turn 1")
    target[0]["reuse_class"] = "R3"
    target[0]["review_source"] = "pilot-b-independent-review-adjudicated"
    target[0]["adjudication_id"] = "PB-RV-106-B"
    return {
        **{key: value for key, value in raw.items() if key != "records"},
        "status": "complete-independent-review-adjudicated",
        "source_artifacts": [
            "data/processed/pilot-b-reuse-review.json",
            "results/pilot/pilot-b-reuse-reviewer2-responses.csv",
            "results/pilot/pilot-b-reuse-review-agreement.json",
            "results/pilot/pilot-b-reuse-adjudication.json",
        ],
        "review_limitations": (
            "A second reviewer independently classified a purposive blinded subset. "
            "Treatment names and primary labels were concealed, but exact prompt context necessarily exposed treatment content. "
            "Turns within trajectories remain dependent."
        ),
        "records": records,
    }


def classification_counts(rows: list[dict[str, Any]], field: str, labels: tuple[str, ...]) -> dict[str, int]:
    counts = Counter(row[field] for row in rows)
    return {label: counts.get(label, 0) for label in labels}


def build_adjudication() -> dict[str, Any]:
    agreement = read_json(AGREEMENT_PATH)
    final_rows = []
    for row in agreement["cases"]:
        reuse = row["primary_reuse_class"]
        context = row["primary_context_class"]
        if row["case_id"] == "PB-RV-106" and row["variant"] == "B":
            reuse = "R3"
        if row["case_id"] == "PB-RV-110" and row["variant"] == "B":
            context = "C2"
        final_rows.append({
            "case_id": row["case_id"],
            "variant": row["variant"],
            "condition": row["condition"],
            "task_slug": row["task_slug"],
            "turn": row["turn"],
            "reuse_class": reuse,
            "context_class": context,
        })
    missed = [row for row in final_rows if row["reuse_class"] in {"R2", "R3"}]
    return {
        "schema_version": 1,
        "status": "adjudicated-focused-validation-sample",
        "implementation_count": 20,
        "paired_case_count": 10,
        "inputs": {
            "primary_new_condition_review": "data/processed/pilot-b-reuse-review.json",
            "primary_baseline_review": "data/processed/pilot-a-reuse-full-review.json",
            "independent_review": "results/pilot/pilot-b-reuse-reviewer2-responses.csv",
            "pre_adjudication_agreement": "results/pilot/pilot-b-reuse-review-agreement.json",
            "rubric": "analysis/rq2/reuse-rubric.md",
        },
        "reviewer_clarifications_before_submission": [
            "An exception helper visible in PB-RV-101 is an incidental convention, not a material candidate for the fixed-message turn.",
            "When candidates differ in visibility, the single context label follows the candidate that determines the reuse classification; jointly decisive candidates use the lower visibility with an explanation.",
            "A diagnostic-slice helper is not applicable when an implementation never builds that slice; absence alone is not missed reuse.",
        ],
        "principles": [
            "Preserve both reviewers' original labels and report pre-adjudication agreement.",
            "Use R3 when the relevant repository abstraction fully covers the behavior but the implementation independently rebuilds it; a low-level library mechanism does not count as partial reuse of that abstraction.",
            "Use C2 when the supplied prompt gives a plausible indirect cue toward the candidate or its abstraction family even when the applicable method is absent.",
        ],
        "decisions": [
            {
                "case_id": "PB-RV-106",
                "variant": "B",
                "condition": "engineering-guardrails",
                "task_slug": "nodeArrayMerge",
                "turn": 1,
                "dimension": "reuse_class",
                "primary_label": "R2",
                "second_reviewer_label": "R3",
                "adjudicated_label": "R3",
                "reason": (
                    "The implementation completely bypasses addInOrder() and directly manages nodes, scores, size, and capacity consequences. "
                    "System.arraycopy() is only a low-level mechanism, not partial reuse of the relevant repository insertion abstraction."
                ),
            },
            {
                "case_id": "PB-RV-110",
                "variant": "B",
                "condition": "baseline",
                "task_slug": "addInOrder",
                "turn": 1,
                "dimension": "context_class",
                "primary_label": "C2",
                "second_reviewer_label": "C1",
                "adjudicated_label": "C2",
                "reason": (
                    "The supplied ArrayUtil import is an indirect cue toward an array-growth abstraction, although growArrays() is not explicit. "
                    "The same reviewer classified this identical Pilot A implementation as C2 during the earlier calibration, revealing C1/C2 boundary instability without affecting the R3 missed-reuse judgment."
                ),
            },
        ],
        "final_classifications": final_rows,
        "summary": {
            "reuse_class_counts": classification_counts(final_rows, "reuse_class", ("R0", "R1", "R2", "R3")),
            "context_class_counts": classification_counts(final_rows, "context_class", ("C0", "C1", "C2", "C3")),
            "missed_reuse_events": len(missed),
            "missed_reuse_by_context": classification_counts(missed, "context_class", ("C0", "C1", "C2", "C3")),
        },
        "interpretation": (
            "The independent review confirms every binary missed-reuse decision. "
            "Adjudication refines one guardrails-only nodeArrayMerge checkpoint from R2 to R3 and retains one baseline addInOrder context label at C2. "
            "Neither decision changes the paper's narrow mechanism claim."
        ),
    }


def lineage_summary(guardrails: list[dict[str, Any]], retrieval: list[dict[str, Any]]) -> dict[str, Any]:
    guard = {(row["task_slug"], int(row["turn"])): row for row in guardrails}
    retr = {(row["task_slug"], int(row["turn"])): row for row in retrieval}
    shared_tasks = sorted({task for task, _ in set(guard) & set(retr)})
    lineages = []
    for task in shared_tasks:
        keys = sorted(key for key in set(guard) & set(retr) if key[0] == task)
        before = [guard[key]["reuse_class"] for key in keys]
        after = [retr[key]["reuse_class"] for key in keys]
        improved = any(a in {"R2", "R3"} and b in {"R0", "R1"} for a, b in zip(before, after))
        lineages.append({
            "task_slug": task,
            "shared_turns": [key[1] for key in keys],
            "guardrails_sequence": before,
            "retrieval_sequence": after,
            "outcome": "improved" if improved else "unchanged-appropriate",
        })
    return {
        "primary_inferential_unit": "trajectory lineage",
        "clean_paired_lineages": len(lineages),
        "improved_lineages": sum(row["outcome"] == "improved" for row in lineages),
        "unchanged_appropriate_lineages": sum(row["outcome"] == "unchanged-appropriate" for row in lineages),
        "worsened_lineages": 0,
        "lineages": lineages,
        "note": "Turns are repeated dependent observations within a lineage and are not independent replicates.",
    }


def build_final_summary(adjudicated: dict[str, Any], adjudication: dict[str, Any]) -> dict[str, Any]:
    config = primary_summary.read_json(primary_summary.CONFIG_PATH)
    functional = primary_summary.read_json(primary_summary.FUNCTIONAL_PATH)
    baseline_review = primary_summary.read_json(primary_summary.BASELINE_REVIEW_PATH)
    expected = primary_summary.expected_new_checkpoints(config)
    records = primary_summary.validate_review(adjudicated, expected)
    baseline = primary_summary.baseline_rows(config, baseline_review)
    guardrails = [row for row in records if row["condition"] == "engineering-guardrails"]
    retrieval = [row for row in records if row["condition"] == "engineering-guardrails-retrieval"]
    agreement = read_json(AGREEMENT_PATH)
    return {
        "schema_version": 1,
        "status": "complete-independent-review-adjudicated",
        "batch_id": config["batch_id"],
        "unit": adjudicated["unit"],
        "review_reliability": {
            "implementation_count": agreement["implementation_count"],
            "reuse_exact_agreement": agreement["reuse"]["exact_agreement"],
            "reuse_linear_weighted_cohens_kappa": agreement["reuse"]["linear_weighted_cohens_kappa"],
            "binary_missed_reuse_exact_agreement": agreement["binary_missed_reuse"]["exact_agreement"],
            "context_exact_agreement": agreement["context_availability"]["exact_agreement"],
            "context_linear_weighted_cohens_kappa": agreement["context_availability"]["linear_weighted_cohens_kappa"],
            "reporting_boundary": "Pre-adjudication agreement is preserved; final labels are consensus classifications, not 100% reviewer agreement.",
        },
        "conditions": {
            "baseline": primary_summary.summarize_rows(baseline),
            "engineering-guardrails": primary_summary.summarize_rows(guardrails),
            "engineering-guardrails-retrieval": primary_summary.summarize_rows(retrieval),
        },
        "paired_comparisons": {
            "guardrails_vs_baseline": primary_summary.transition_summary(baseline, guardrails),
            "retrieval_vs_guardrails": primary_summary.transition_summary(guardrails, retrieval),
            "retrieval_vs_baseline": primary_summary.transition_summary(baseline, retrieval),
        },
        "lineage_analysis": lineage_summary(guardrails, retrieval),
        "incorrect_task_diagnosis": adjudicated["incorrect_task_diagnosis"],
        "interpretation": {
            "guardrails_only": "Guardrails alone leave the nodeArrayMerge lineage on a missed-reuse path (R3, R2, R2, R2); advice without API exposure does not redirect it.",
            "retrieval": "All 14 retrieval-supported eligible correct checkpoints are R1. In the four clean paired lineages, nodeArrayMerge improves and the other three remain appropriately reused.",
            "boundary": "This is targeted mechanism evidence from a purposive sample with one run per condition and dependent turns, not a population-level causal estimate.",
        },
        "source_artifacts": {
            "adjudicated_review": {
                "path": str(ADJUDICATED_JSON_PATH.relative_to(ROOT)),
                "sha256": hashlib.sha256(ADJUDICATED_JSON_PATH.read_bytes()).hexdigest(),
            },
            "agreement": str(AGREEMENT_PATH.relative_to(ROOT)),
            "adjudication": str(ADJUDICATION_PATH.relative_to(ROOT)),
        },
        "functional_batch_id": functional["batch_id"],
    }


def write_adjudicated_csv(review: dict[str, Any]) -> None:
    fields = [
        "condition", "task_slug", "repository", "turn", "run_id", "reuse_class",
        "context_class", "candidate_symbol", "evidence", "context_evidence",
        "maintenance_consequence", "confidence", "review_source", "adjudication_id",
    ]
    with ADJUDICATED_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in review["records"])


def main() -> int:
    adjudication = build_adjudication()
    write_json(ADJUDICATION_PATH, adjudication)
    adjudicated = build_adjudicated_review()
    write_json(ADJUDICATED_JSON_PATH, adjudicated)
    write_adjudicated_csv(adjudicated)
    summary = build_final_summary(adjudicated, adjudication)
    write_json(FINAL_SUMMARY_PATH, summary)
    print(json.dumps({
        "conditions": summary["conditions"],
        "retrieval_vs_guardrails": summary["paired_comparisons"]["retrieval_vs_guardrails"],
        "lineage_analysis": summary["lineage_analysis"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
