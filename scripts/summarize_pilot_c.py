#!/usr/bin/env python3
"""Summarize Pilot C functional yield and repository-API uptake."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_pilot_c  # noqa: E402
import pilot_a  # noqa: E402
import pilot_c  # noqa: E402
import run_pilot_c  # noqa: E402


OUTPUT_JSON = ROOT / "results/pilot/pilot-c-functional-reuse-summary.json"
OUTPUT_MD = ROOT / "analysis/rq2/pilot-c-findings.md"


def failure_class(turn: dict[str, Any]) -> str:
    if turn.get("cumulatively_correct") is True:
        return "pass"
    detail = "\n".join(str(test.get("detail") or "") for test in turn.get("tests", []))
    if "COMPILATION ERROR" in detail or "cannot find symbol" in detail or "no suitable method found" in detail:
        return "compilation"
    if "Unused import" in detail or "checkstyle" in detail.lower():
        return "repository-style-gate"
    if "AssertionError" in detail or "There are test failures" in detail:
        return "behavioral-contract"
    return "other"


def symbol_coverage(code: str, symbols: list[str]) -> int:
    needles = {
        "REQUEST_FIELD_NAMES_PER_CLASS": "REQUEST_FIELD_NAMES_PER_CLASS",
        "objectToMap(Object)": "objectToMap(",
        "mapToClass(Map<String, Object>, Class<T>)": "mapToClass(",
        "getJsonPropertyValues(Class<?>)": "getJsonPropertyValues",
        "loadDocuments(Stream<Path>, PathMatcher, Path, DocumentParser)": "loadDocuments(",
    }
    return sum(needles[symbol] in code for symbol in symbols)


def build_summary() -> dict[str, Any]:
    config = pilot_c.read_json(pilot_c.DEFAULT_CONFIG)
    errors = pilot_c.validate_config(config, check_dataset=True)
    if errors:
        raise RuntimeError("Invalid Pilot C configuration:\n- " + "\n- ".join(errors))

    rows: list[dict[str, Any]] = []
    for condition in run_pilot_c.NEW_CONDITIONS:
        for task in config["tasks"]:
            for repetition in range(1, config["runs_per_task_condition"] + 1):
                path = evaluate_pilot_c.record_path(config, task, condition, repetition)
                record = pilot_a.read_json(path)
                evaluate_pilot_c.validate_record(record, config, task, condition, repetition)
                for turn in record["turns"]:
                    coverage = symbol_coverage(turn["extracted_code"], task["retrieval_symbols"])
                    rows.append(
                        {
                            "run_id": record["run_id"],
                            "repo": task["repo"],
                            "task": task["slug"],
                            "condition": condition,
                            "repetition": repetition,
                            "turn": turn["turn"],
                            "cumulatively_correct": turn["cumulatively_correct"],
                            "failure_class": failure_class(turn),
                            "candidate_symbols_present": coverage,
                            "candidate_symbols_total": len(task["retrieval_symbols"]),
                            "all_candidate_symbols_present": coverage == len(task["retrieval_symbols"]),
                            "candidate_helper_reused": (
                                task["slug"] == "loadDocumentsRecursively" and coverage == 1
                            ),
                        }
                    )

    checks = [
        test
        for condition in run_pilot_c.NEW_CONDITIONS
        for task in config["tasks"]
        for repetition in range(1, config["runs_per_task_condition"] + 1)
        for turn in pilot_a.read_json(
            evaluate_pilot_c.record_path(config, task, condition, repetition)
        )["turns"]
        for test in turn["tests"]
    ]
    by_condition: dict[str, Any] = {}
    for condition in run_pilot_c.NEW_CONDITIONS:
        subset = [row for row in rows if row["condition"] == condition]
        by_condition[condition] = {
            "checkpoints": len(subset),
            "cumulatively_correct_checkpoints": sum(row["cumulatively_correct"] is True for row in subset),
            "fully_exposed_candidate_checkpoints": sum(row["all_candidate_symbols_present"] for row in subset),
            "failure_classes": dict(sorted(Counter(row["failure_class"] for row in subset).items())),
        }
    by_repository: dict[str, Any] = {}
    for repo in sorted({row["repo"] for row in rows}):
        subset = [row for row in rows if row["repo"] == repo]
        by_repository[repo] = {
            "checkpoints": len(subset),
            "cumulatively_correct_checkpoints": sum(row["cumulatively_correct"] is True for row in subset),
            "failure_classes": dict(sorted(Counter(row["failure_class"] for row in subset).items())),
        }

    langchain = [row for row in rows if row["task"] == "loadDocumentsRecursively"]
    spring = [row for row in rows if row["task"] == "merge"]
    return {
        "schema_version": 1,
        "batch_id": config["batch_id"],
        "design": {
            "repositories": 2,
            "tasks": 2,
            "conditions": 2,
            "repetitions_per_task_condition": 3,
            "trajectories": 12,
            "checkpoints": 24,
        },
        "functional": {
            "passed_checks": sum(test["status"] == "pass" for test in checks),
            "failed_checks": sum(test["status"] == "fail" for test in checks),
            "cumulatively_correct_checkpoints": sum(row["cumulatively_correct"] is True for row in rows),
            "ineligible_checkpoints": sum(row["cumulatively_correct"] is not True for row in rows),
            "by_condition": by_condition,
            "by_repository": by_repository,
        },
        "reuse": {
            "primary_eligible_checkpoints": len(langchain),
            "primary_r1_checkpoints": sum(row["candidate_helper_reused"] for row in langchain),
            "primary_result": "All eligible checkpoints reused the repository stream helper in both conditions.",
            "spring_ai_diagnostic_only": {
                condition: {
                    "checkpoints": len([row for row in spring if row["condition"] == condition]),
                    "all_four_packet_symbols_present": sum(
                        row["all_candidate_symbols_present"]
                        for row in spring
                        if row["condition"] == condition
                    ),
                }
                for condition in run_pilot_c.NEW_CONDITIONS
            },
        },
        "interpretation": [
            "The LangChain4j case replicates reliable repository-helper reuse but has a ceiling in both conditions, so it does not identify a retrieval increment.",
            "The Spring AI packet increased complete candidate-symbol uptake from 1/6 to 6/6 checkpoints, but all Spring AI checkpoints remained functionally ineligible.",
            "Pilot C therefore supports the narrow mechanism distinction that explicit context changes API uptake, while showing that API visibility alone is insufficient for functional repository fit.",
            "The two tasks do not support a broad cross-repository causal effect claim.",
        ],
        "checkpoints": rows,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    functional = summary["functional"]
    reuse = summary["reuse"]
    return f"""# Pilot C cross-repository findings

Pilot C completed all 12 frozen trajectories (24 checkpoints). The cumulative
functional gate passed {functional['passed_checks']} of {functional['passed_checks'] + functional['failed_checks']}
test executions; {functional['cumulatively_correct_checkpoints']} of 24
checkpoints were eligible for primary reuse analysis.

| Repository/task | Guardrails correct | Retrieval correct | Interpretation |
|---|---:|---:|---|
| LangChain4j `loadDocumentsRecursively` | 6/6 | 6/6 | All 12 checkpoints reused the repository stream helper (R1); ceiling in both conditions. |
| Spring AI `merge` | 0/6 | 0/6 | Ineligible: compilation, repository-style, or exact behavioral-contract failures. |

For Spring AI, the retrieval packet changed repository-API uptake even though
it did not restore correctness: all four supplied symbols appeared in
{reuse['spring_ai_diagnostic_only']['engineering-guardrails-retrieval']['all_four_packet_symbols_present']}/6 retrieval checkpoints versus
{reuse['spring_ai_diagnostic_only']['engineering-guardrails']['all_four_packet_symbols_present']}/6 guardrails-only checkpoints. This is diagnostic evidence, not a primary reuse
result, because none of those checkpoints passed the functional gate.

The defensible conclusion is narrow: making repository APIs explicit can make
the model use them, but API visibility alone does not guarantee repository-fit
correctness. This replication does not establish a broad cross-repository
causal effect; one task is a reuse ceiling and the other has zero eligible
checkpoints.
"""


def main() -> int:
    summary = build_summary()
    pilot_a.write_json(OUTPUT_JSON, summary)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(render_markdown(summary), encoding="utf-8")
    print(f"Summary: {OUTPUT_JSON}")
    print(f"Findings: {OUTPUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
