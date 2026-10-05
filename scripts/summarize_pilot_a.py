#!/usr/bin/env python3
"""Build the clean Pilot A functional view with amendment substitutions."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "experiment/config/protocol.json"
MANIFEST_PATH = ROOT / "experiment/config/pilot-tasks.json"
AMENDMENT_PATH = ROOT / "experiment/config/pilot-a-amendment.json"
AUDIT_PATH = ROOT / "results/pilot/prompt-context-sufficiency-audit.json"
REPORT_DIR = ROOT / "results/pilot/generated-tests"
OUTPUT_PATH = ROOT / "results/pilot/pilot-a-adjusted-functional-summary.json"
PUBLIC_MANIFEST_PATH = ROOT / "MANIFEST.json"

REFERENCE_INELIGIBLE = {
    "nodeArrayMerge": {5},
    "randomAccessScoreProvider": {4},
    "methodToProperty": {2, 3},
    "underlineToCamel": {2, 3},
    "loadDocuments": {2, 3},
}
PROMPT_CONFOUNDED = {"set": {1}}


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
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
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


def amendment_tasks(amendment: dict[str, Any]) -> list[dict[str, Any]]:
    replacements = amendment.get("replacements")
    if not isinstance(replacements, list):
        raise SummaryError("Amendment replacements must be an array")
    tasks = [replacement.get("task") for replacement in replacements]
    if any(not isinstance(task, dict) for task in tasks):
        raise SummaryError("Every amendment replacement must contain a task")
    return tasks


def context_sensitivity_exclusions(audit: dict[str, Any]) -> dict[str, set[int]]:
    exclusions: dict[str, set[int]] = {}
    for task in audit.get("tasks", []):
        if task.get("analysis_action") == "retain-frozen-primary-exclude-context-sensitivity":
            exclusions[task["slug"]] = set(task["affected_turns"])
    return exclusions


def strict_signature_exclusions(
    audit: dict[str, Any], task_metadata: dict[str, dict[str, Any]]
) -> dict[str, set[int]]:
    excluded_classes = {"inferable-consistent", "underspecified-integration-types"}
    return {
        task["slug"]: set(range(1, task_metadata[task["slug"]]["turns"] + 1))
        for task in audit.get("tasks", [])
        if task.get("classification") in excluded_classes
    }


def is_eligible(slug: str, turn: int) -> tuple[bool, str | None]:
    if turn in REFERENCE_INELIGIBLE.get(slug, set()):
        return False, "reference-ineligible"
    if turn in PROMPT_CONFOUNDED.get(slug, set()):
        return False, "prompt-confounded"
    return True, None


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
    tests = checkpoint.get("tests")
    if not isinstance(tests, list):
        raise SummaryError("Checkpoint tests must be an array")
    turn = checkpoint.get("turn")
    counts["checkpoints"] += 1
    counts["cumulatively_correct_checkpoints"] += int(
        checkpoint.get("cumulatively_correct") is True
    )
    counts["checks"] += len(tests)
    counts["passed_checks"] += sum(test.get("status") == "pass" for test in tests)
    counts["failed_checks"] += sum(test.get("status") == "fail" for test in tests)
    same_turn = [test for test in tests if test.get("test_turn") == turn]
    if len(same_turn) != 1:
        raise SummaryError(f"Checkpoint {turn} has {len(same_turn)} same-turn tests")
    counts["same_turn_passed"] += int(same_turn[0].get("status") == "pass")
    counts["same_turn_failed"] += int(same_turn[0].get("status") == "fail")


def build_summary(
    protocol: dict[str, Any],
    manifest: dict[str, Any],
    amendment: dict[str, Any],
    audit: dict[str, Any],
    original_report: dict[str, Any],
    amendment_report: dict[str, Any],
) -> dict[str, Any]:
    original_batch = protocol["pilot_a"]["batch_id"]
    amendment_batch = amendment["batch_id"]
    if original_report.get("batch_id") != original_batch:
        raise SummaryError("Original report batch ID mismatch")
    if amendment_report.get("batch_id") != amendment_batch:
        raise SummaryError("Amendment report batch ID mismatch")

    original_tasks = {task["slug"]: task for task in manifest["tasks"]}
    replacement_rows = amendment["replacements"]
    replaced_slugs = {row["replaces"]["slug"] for row in replacement_rows}
    replacement_for = {row["task"]["slug"]: row["replaces"]["slug"] for row in replacement_rows}
    task_metadata = {
        slug: task for slug, task in original_tasks.items() if slug not in replaced_slugs
    }
    task_metadata.update({task["slug"]: task for task in amendment_tasks(amendment)})

    original_results = {
        task["slug"]: task
        for task in original_report["tasks"]
        if task["slug"] not in replaced_slugs
    }
    amendment_results = {task["slug"]: task for task in amendment_report["tasks"]}
    adjusted_results = {**original_results, **amendment_results}
    if set(adjusted_results) != set(task_metadata):
        raise SummaryError("Adjusted report tasks do not match adjusted task metadata")

    raw = empty_counts()
    eligible = empty_counts()
    context_robust = empty_counts()
    strict_explicit = empty_counts()
    by_repository: dict[str, dict[str, int]] = {}
    by_turn: dict[str, dict[str, int]] = {}
    context_by_repository: dict[str, dict[str, int]] = {}
    context_by_turn: dict[str, dict[str, int]] = {}
    strict_by_repository: dict[str, dict[str, int]] = {}
    strict_by_turn: dict[str, dict[str, int]] = {}
    exclusions: list[dict[str, Any]] = []
    context_exclusions: list[dict[str, Any]] = []
    strict_exclusions: list[dict[str, Any]] = []
    task_rows: list[dict[str, Any]] = []
    trajectories_with_correct = 0
    eligible_trajectories_with_correct = 0
    context_trajectories_with_correct = 0
    context_tasks_with_checkpoints = 0
    strict_trajectories_with_correct = 0
    strict_tasks_with_checkpoints = 0
    context_exclusion_map = context_sensitivity_exclusions(audit)
    strict_exclusion_map = strict_signature_exclusions(audit, task_metadata)

    for slug, task in task_metadata.items():
        result = adjusted_results[slug]
        repo = task["repo"]
        task_raw = empty_counts()
        task_eligible = empty_counts()
        task_context_robust = empty_counts()
        task_strict_explicit = empty_counts()
        for checkpoint in result["checkpoints"]:
            turn = int(checkpoint["turn"])
            add_checkpoint(raw, checkpoint)
            add_checkpoint(task_raw, checkpoint)
            checkpoint_eligible, reason = is_eligible(slug, turn)
            if checkpoint_eligible:
                add_checkpoint(eligible, checkpoint)
                add_checkpoint(task_eligible, checkpoint)
                add_checkpoint(by_repository.setdefault(repo, empty_counts()), checkpoint)
                add_checkpoint(by_turn.setdefault(str(turn), empty_counts()), checkpoint)
                if turn in context_exclusion_map.get(slug, set()):
                    context_exclusions.append(
                        {
                            "slug": slug,
                            "turn": turn,
                            "reason": "post-generation-context-underspecified",
                            "checks_removed": len(checkpoint["tests"]),
                        }
                    )
                else:
                    add_checkpoint(context_robust, checkpoint)
                    add_checkpoint(task_context_robust, checkpoint)
                    add_checkpoint(
                        context_by_repository.setdefault(repo, empty_counts()), checkpoint
                    )
                    add_checkpoint(
                        context_by_turn.setdefault(str(turn), empty_counts()), checkpoint
                    )
                if turn in strict_exclusion_map.get(slug, set()):
                    strict_exclusions.append(
                        {
                            "slug": slug,
                            "turn": turn,
                            "reason": "post-generation-no-literal-signature",
                            "checks_removed": len(checkpoint["tests"]),
                        }
                    )
                else:
                    add_checkpoint(strict_explicit, checkpoint)
                    add_checkpoint(task_strict_explicit, checkpoint)
                    add_checkpoint(
                        strict_by_repository.setdefault(repo, empty_counts()), checkpoint
                    )
                    add_checkpoint(
                        strict_by_turn.setdefault(str(turn), empty_counts()), checkpoint
                    )
            else:
                exclusions.append(
                    {
                        "slug": slug,
                        "turn": turn,
                        "reason": reason,
                        "checks_removed": len(checkpoint["tests"]),
                    }
                )
        has_correct = task_raw["cumulatively_correct_checkpoints"] > 0
        has_eligible_correct = task_eligible["cumulatively_correct_checkpoints"] > 0
        has_context_correct = task_context_robust["cumulatively_correct_checkpoints"] > 0
        has_strict_correct = task_strict_explicit["cumulatively_correct_checkpoints"] > 0
        trajectories_with_correct += int(has_correct)
        eligible_trajectories_with_correct += int(has_eligible_correct)
        context_trajectories_with_correct += int(has_context_correct)
        context_tasks_with_checkpoints += int(task_context_robust["checkpoints"] > 0)
        strict_trajectories_with_correct += int(has_strict_correct)
        strict_tasks_with_checkpoints += int(task_strict_explicit["checkpoints"] > 0)
        task_rows.append(
            {
                "slug": slug,
                "repo": repo,
                "source_batch_id": amendment_batch if slug in amendment_results else original_batch,
                "replaces": replacement_for.get(slug),
                "raw": task_raw,
                "eligible": task_eligible,
                "context_robust": task_context_robust,
                "strict_explicit_signature": task_strict_explicit,
            }
        )

    raw["tasks"] = len(adjusted_results)
    raw["trajectories_with_correct_checkpoint"] = trajectories_with_correct
    eligible["tasks"] = len(adjusted_results)
    eligible["trajectories_with_correct_checkpoint"] = eligible_trajectories_with_correct
    context_robust["tasks"] = len(adjusted_results)
    context_robust["tasks_with_eligible_checkpoints"] = context_tasks_with_checkpoints
    context_robust["trajectories_with_correct_checkpoint"] = (
        context_trajectories_with_correct
    )
    strict_explicit["tasks"] = len(adjusted_results)
    strict_explicit["tasks_with_eligible_checkpoints"] = strict_tasks_with_checkpoints
    strict_explicit["trajectories_with_correct_checkpoint"] = (
        strict_trajectories_with_correct
    )

    if raw["checkpoints"] != 70 or raw["checks"] != 176:
        raise SummaryError("Adjusted Pilot A must retain 70 checkpoints and 176 checks")
    if len(exclusions) != 9:
        raise SummaryError(f"Expected 9 excluded checkpoints, found {len(exclusions)}")
    if len(context_exclusions) != audit["summary"]["new_sensitivity_excluded_checkpoints"]:
        raise SummaryError(
            f"Expected {audit['summary']['new_sensitivity_excluded_checkpoints']} context "
            f"sensitivity exclusions, found {len(context_exclusions)}"
        )
    if len(strict_exclusions) != audit["summary"][
        "strict_explicit_signature_excluded_checkpoints"
    ]:
        raise SummaryError(
            "Strict explicit-signature sensitivity exclusion count mismatch"
        )

    return {
        "schema_version": 2,
        "created_at": frozen_created_at(OUTPUT_PATH),
        "original_batch_id": original_batch,
        "amendment_batch_id": amendment_batch,
        "substitutions": [
            {
                "removed": row["replaces"]["slug"],
                "added": row["task"]["slug"],
            }
            for row in replacement_rows
        ],
        "raw_adjusted": raw,
        "primary_eligible": eligible,
        "exclusions": exclusions,
        "eligible_by_repository": by_repository,
        "eligible_by_turn": by_turn,
        "context_sufficiency_sensitivity": {
            "audit_timing": audit["audit_timing"],
            "interpretation": (
                "Post-generation sensitivity view only; it does not replace the frozen "
                "primary result."
            ),
            "counts": context_robust,
            "new_exclusions": context_exclusions,
            "eligible_by_repository": context_by_repository,
            "eligible_by_turn": context_by_turn,
        },
        "strict_explicit_signature_sensitivity": {
            "audit_timing": audit["audit_timing"],
            "interpretation": (
                "Conservative post-generation sensitivity view retaining only tasks whose "
                "integration-critical signature was supplied literally."
            ),
            "counts": strict_explicit,
            "new_exclusions": strict_exclusions,
            "eligible_by_repository": strict_by_repository,
            "eligible_by_turn": strict_by_turn,
        },
        "tasks": task_rows,
        "functional_gate_decision": {
            "outcome": "PROCEED",
            "meaning": "Proceed to structural and reuse feasibility analysis on eligible correct checkpoints.",
            "final_pilot_outcome": "pending",
            "rationale": (
                "The clean adjusted sample retains functionally correct checkpoints across "
                "multiple trajectories and turns, and the prompt-context sensitivities do "
                "not reverse that conclusion. GO/NARROW/PIVOT remains pending because the "
                "frozen rule also requires structural variation and operationalizable "
                "missed-reuse judgments."
            ),
        },
    }


def main() -> int:
    try:
        protocol = read_json(PROTOCOL_PATH)
        manifest = read_json(MANIFEST_PATH)
        amendment = read_json(AMENDMENT_PATH)
        audit = read_json(AUDIT_PATH)
        original_report = read_json(REPORT_DIR / f"{protocol['pilot_a']['batch_id']}.json")
        amendment_report = read_json(REPORT_DIR / f"{amendment['batch_id']}.json")
        summary = build_summary(
            protocol, manifest, amendment, audit, original_report, amendment_report
        )
        source_paths = [
            REPORT_DIR / f"{protocol['pilot_a']['batch_id']}.json",
            REPORT_DIR / f"{amendment['batch_id']}.json",
            AUDIT_PATH,
            *sorted((ROOT / "data/generated-trajectories/pilot-a").glob("*/record.json")),
            *sorted(
                (ROOT / "data/generated-trajectories/pilot-a-amendment").glob(
                    "*/record.json"
                )
            ),
        ]
        if len(source_paths) != 23:
            raise SummaryError(f"Expected 23 source artifacts, found {len(source_paths)}")
        summary["source_artifacts"] = [artifact_digest(path) for path in source_paths]
        write_json(OUTPUT_PATH, summary)
        print(json.dumps(summary["raw_adjusted"], sort_keys=True))
        print(json.dumps(summary["primary_eligible"], sort_keys=True))
        print(
            json.dumps(
                summary["context_sufficiency_sensitivity"]["counts"], sort_keys=True
            )
        )
        print(
            json.dumps(
                summary["strict_explicit_signature_sensitivity"]["counts"],
                sort_keys=True,
            )
        )
        print(f"Report: {OUTPUT_PATH}")
        return 0
    except (SummaryError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
