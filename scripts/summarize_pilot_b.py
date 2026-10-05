#!/usr/bin/env python3
"""Build the durable three-condition Pilot B functional summary."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "experiment/config/pilot-b.json"
REPORT_DIR = ROOT / "results/pilot/generated-tests"
OUTPUT_PATH = ROOT / "results/pilot/pilot-b-functional-summary.json"
PUBLIC_MANIFEST_PATH = ROOT / "MANIFEST.json"

NEW_CONDITIONS = (
    "engineering-guardrails",
    "engineering-guardrails-retrieval",
)
REFERENCE_INELIGIBLE = {
    "loadDocuments": {2, 3},
    "nodeArrayMerge": {5},
    "randomAccessScoreProvider": {4},
}


class SummaryError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SummaryError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SummaryError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def artifact_digest(path: Path) -> dict[str, Any]:
    relative = path.relative_to(ROOT).as_posix()
    if PUBLIC_MANIFEST_PATH.exists():
        manifest = read_json(PUBLIC_MANIFEST_PATH)
        item = next(
            (candidate for candidate in manifest.get("files", []) if candidate.get("path") == relative),
            None,
        )
        if item and "source_sha256" in item and "source_bytes" in item:
            return {
                "path": relative,
                "sha256": item["source_sha256"],
                "bytes": item["source_bytes"],
            }
    return {
        "path": relative,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def frozen_created_at(path: Path) -> str:
    if path.exists():
        value = read_json(path).get("created_at")
        if isinstance(value, str) and value:
            return value
    return dt.datetime.now(dt.timezone.utc).isoformat()


def empty_counts() -> dict[str, int]:
    return {
        "checkpoints": 0,
        "cumulatively_correct_checkpoints": 0,
        "checks": 0,
        "passed_checks": 0,
        "failed_checks": 0,
        "same_turn_passed": 0,
        "same_turn_failed": 0,
    }


def add_checkpoint(counts: dict[str, int], checkpoint: dict[str, Any]) -> None:
    turn = checkpoint.get("turn")
    tests = checkpoint.get("tests")
    if not isinstance(turn, int) or not isinstance(tests, list):
        raise SummaryError("Every checkpoint must have an integer turn and tests array")
    expected_test_turns = set(range(1, turn + 1))
    actual_test_turns = {test.get("test_turn") for test in tests}
    if actual_test_turns != expected_test_turns:
        raise SummaryError(
            f"Checkpoint {turn} test turns {actual_test_turns} do not match "
            f"{expected_test_turns}"
        )
    statuses = [test.get("status") for test in tests]
    if any(status not in {"pass", "fail"} for status in statuses):
        raise SummaryError(f"Checkpoint {turn} has an unknown test status")
    correct = all(status == "pass" for status in statuses)
    if checkpoint.get("cumulatively_correct") is not correct:
        raise SummaryError(f"Checkpoint {turn} cumulative flag does not match its tests")

    counts["checkpoints"] += 1
    counts["cumulatively_correct_checkpoints"] += int(correct)
    counts["checks"] += len(tests)
    counts["passed_checks"] += sum(status == "pass" for status in statuses)
    counts["failed_checks"] += sum(status == "fail" for status in statuses)
    same_turn_status = next(
        test["status"] for test in tests if test["test_turn"] == turn
    )
    counts[f"same_turn_{'passed' if same_turn_status == 'pass' else 'failed'}"] += 1


def checkpoints_from_record(record: dict[str, Any]) -> list[dict[str, Any]]:
    turns = record.get("turns")
    if not isinstance(turns, list):
        raise SummaryError(f"{record.get('run_id')}: turns must be an array")
    return [
        {
            "turn": turn.get("turn"),
            "cumulatively_correct": turn.get("cumulatively_correct"),
            "tests": turn.get("tests"),
        }
        for turn in turns
    ]


def summarize_condition(
    config: dict[str, Any],
    condition: str,
    results: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    expected_slugs = [task["slug"] for task in config["tasks"]]
    if set(results) != set(expected_slugs):
        raise SummaryError(f"{condition}: task set does not match the frozen config")

    raw = empty_counts()
    eligible = empty_counts()
    task_rows = []
    raw_trajectories = 0
    eligible_trajectories = 0
    for task in config["tasks"]:
        slug = task["slug"]
        checkpoints = results[slug]
        if len(checkpoints) != task["turns"]:
            raise SummaryError(f"{condition}/{slug}: unexpected checkpoint count")
        task_raw = empty_counts()
        task_eligible = empty_counts()
        excluded_turns = REFERENCE_INELIGIBLE.get(slug, set())
        for checkpoint in checkpoints:
            add_checkpoint(raw, checkpoint)
            add_checkpoint(task_raw, checkpoint)
            if checkpoint["turn"] not in excluded_turns:
                add_checkpoint(eligible, checkpoint)
                add_checkpoint(task_eligible, checkpoint)
        raw_trajectories += int(task_raw["cumulatively_correct_checkpoints"] > 0)
        eligible_trajectories += int(
            task_eligible["cumulatively_correct_checkpoints"] > 0
        )
        task_rows.append(
            {
                "slug": slug,
                "repo": task["repo"],
                "raw": task_raw,
                "primary_eligible": task_eligible,
            }
        )

    raw["tasks"] = len(task_rows)
    raw["trajectories_with_correct_checkpoint"] = raw_trajectories
    eligible["tasks"] = len(task_rows)
    eligible["trajectories_with_correct_checkpoint"] = eligible_trajectories
    return {
        "condition": condition,
        "raw": raw,
        "primary_eligible": eligible,
        "tasks": task_rows,
    }


def count_delta(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    fields = (
        "passed_checks",
        "failed_checks",
        "cumulatively_correct_checkpoints",
        "same_turn_passed",
        "same_turn_failed",
        "trajectories_with_correct_checkpoint",
    )
    return {field: after[field] - before[field] for field in fields}


def build_summary(
    config: dict[str, Any],
    baseline_records: dict[str, dict[str, Any]],
    reports: dict[str, dict[str, Any]],
    new_records: list[dict[str, Any]],
) -> dict[str, Any]:
    batch_id = config["batch_id"]
    baseline_results: dict[str, list[dict[str, Any]]] = {}
    for task in config["tasks"]:
        record = baseline_records[task["slug"]]
        if record.get("run_id") != task["baseline_run_id"]:
            raise SummaryError(f"{task['slug']}: baseline run ID mismatch")
        baseline_results[task["slug"]] = checkpoints_from_record(record)

    condition_results = {"baseline": baseline_results}
    for condition in NEW_CONDITIONS:
        report = reports[condition]
        if report.get("batch_id") != batch_id or report.get("condition") != condition:
            raise SummaryError(f"{condition}: functional report identity mismatch")
        condition_results[condition] = {
            task["slug"]: task["checkpoints"] for task in report["tasks"]
        }

    condition_rows = {
        condition: summarize_condition(config, condition, results)
        for condition, results in condition_results.items()
    }
    baseline = condition_rows["baseline"]
    guardrails = condition_rows["engineering-guardrails"]
    retrieval = condition_rows["engineering-guardrails-retrieval"]

    sessions = [record.get("session_id") for record in new_records]
    if len(new_records) != 12 or len(set(sessions)) != 12 or None in sessions:
        raise SummaryError("Expected 12 new records with 12 distinct session IDs")
    generated_turns = sum(len(record.get("turns", [])) for record in new_records)
    if generated_turns != 46:
        raise SummaryError(f"Expected 46 generated turns, found {generated_turns}")
    if any(record.get("completed_at") is None for record in new_records):
        raise SummaryError("At least one Pilot B generation record is incomplete")

    exclusions = [
        {
            "slug": slug,
            "turn": turn,
            "reason": "reference-ineligible",
            "checks_removed": turn,
        }
        for slug, turns in REFERENCE_INELIGIBLE.items()
        for turn in sorted(turns)
    ]
    comparisons = {}
    for name, after, before in (
        ("prompting_effect", guardrails, baseline),
        ("retrieval_increment", retrieval, guardrails),
        ("combined_intervention", retrieval, baseline),
    ):
        comparisons[name] = {
            "contrast": config["comparisons"][name],
            "raw_delta": count_delta(after["raw"], before["raw"]),
            "primary_eligible_delta": count_delta(
                after["primary_eligible"], before["primary_eligible"]
            ),
        }

    return {
        "schema_version": 1,
        "created_at": frozen_created_at(OUTPUT_PATH),
        "batch_id": batch_id,
        "study_role": config["study_role"],
        "generation_integrity": {
            "new_trajectories": len(new_records),
            "generated_turns": generated_turns,
            "unique_sessions": len(set(sessions)),
            "model_response_retries": 0,
            "test_feedback_to_model": False,
        },
        "primary_eligibility": {
            "rule": "Apply the frozen Pilot A reference-eligibility exclusions identically to all three conditions.",
            "excluded_checkpoints": exclusions,
        },
        "conditions": [condition_rows[name] for name in ("baseline", *NEW_CONDITIONS)],
        "comparisons": comparisons,
        "interpretation": {
            "guardrails_only": (
                "No aggregate functional improvement over the existing baseline; "
                "the eligible cumulative total changes from 10/19 to 9/19."
            ),
            "retrieval_increment": (
                "The retrieval condition improves the eligible cumulative total from "
                "9/19 to 14/19, concentrated in diff (+4) and addInOrder (+1)."
            ),
            "limitations": (
                "This is an outcome-informed exploratory mechanism probe with one run per "
                "task and condition. Checkpoints within a trajectory are dependent, and "
                "the result is not a population-level causal estimate."
            ),
        },
    }


def find_record(run_id: str) -> Path:
    matches = list((ROOT / "data/generated-trajectories").glob(f"**/{run_id}/record.json"))
    if len(matches) != 1:
        raise SummaryError(f"Expected one record for {run_id}, found {len(matches)}")
    return matches[0]


def main() -> int:
    try:
        config = read_json(CONFIG_PATH)
        baseline_paths = {
            task["slug"]: find_record(task["baseline_run_id"])
            for task in config["tasks"]
        }
        baseline_records = {
            slug: read_json(path) for slug, path in baseline_paths.items()
        }
        report_paths = {
            condition: REPORT_DIR / f"{config['batch_id']}-{condition}.json"
            for condition in NEW_CONDITIONS
        }
        reports = {condition: read_json(path) for condition, path in report_paths.items()}
        new_record_paths = sorted(
            (ROOT / "data/generated-trajectories/pilot-b").glob(
                f"{config['batch_id']}-*/record.json"
            )
        )
        new_records = [read_json(path) for path in new_record_paths]
        summary = build_summary(config, baseline_records, reports, new_records)
        source_paths = [
            CONFIG_PATH,
            *baseline_paths.values(),
            *report_paths.values(),
            *new_record_paths,
        ]
        if len(source_paths) != 21:
            raise SummaryError(f"Expected 21 source artifacts, found {len(source_paths)}")
        summary["source_artifacts"] = [artifact_digest(path) for path in source_paths]
        write_json(OUTPUT_PATH, summary)
        for row in summary["conditions"]:
            print(row["condition"], json.dumps(row["primary_eligible"], sort_keys=True))
        print(f"Report: {OUTPUT_PATH}")
        return 0
    except (SummaryError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
