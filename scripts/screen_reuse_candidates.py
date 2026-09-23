#!/usr/bin/env python3
"""Screen functionally correct Pilot A checkpoints for reuse candidates.

The screen is deliberately high-recall. A reference-only call is evidence for
manual inspection, not proof that the generated implementation missed reuse.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "data/processed/pilot-a-structural-metrics.json"
PACKET_DIR = ROOT / "work/task-packets"
AMENDMENT_PACKET_DIR = ROOT / "work/amendment-task-packets"
CSV_OUTPUT = ROOT / "data/processed/pilot-a-reuse-candidates.csv"
JSON_OUTPUT = ROOT / "data/processed/pilot-a-reuse-candidates.json"
SUMMARY_OUTPUT = ROOT / "results/pilot/pilot-a-reuse-screen-summary.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def packet_for(slug: str) -> dict[str, Any]:
    candidates = (AMENDMENT_PACKET_DIR / f"{slug}.json", PACKET_DIR / f"{slug}.json")
    for path in candidates:
        if path.is_file():
            return read_json(path)
    raise FileNotFoundError(f"No task packet for {slug}")


def name_occurrences(text: str, name: str) -> int:
    return len(re.findall(rf"\b{re.escape(name)}\b", text))


def callable_occurrences(text: str, name: str) -> int:
    """Count call-shaped mentions and avoid prose such as 'scale the row'."""
    return len(re.findall(rf"\b{re.escape(name)}\s*\(", text))


def screen_record(record: dict[str, Any]) -> dict[str, Any]:
    slug = record["task_slug"]
    turn = int(record["turn"])
    packet = packet_for(slug)
    instructions = "\n".join(
        item["instruction"]
        for item in packet["turn_datas"]
        if int(item["turn_num"]) <= turn
    )
    context = packet["metadata"]["context"]
    generated_calls = set(record["generated"]["method_call_targets"])
    reference_calls = set(record["reference"]["method_call_targets"])
    reference_only = sorted(reference_calls - generated_calls)
    generated_only = sorted(generated_calls - reference_calls)

    call_evidence = []
    for name in reference_only:
        instruction_count = callable_occurrences(instructions, name)
        context_count = callable_occurrences(context, name)
        if instruction_count:
            visibility = "instruction-explicit"
            priority = 3
        elif context_count:
            visibility = "initial-context-visible"
            priority = 2
        else:
            visibility = "reference-only-latent"
            priority = 1
        call_evidence.append(
            {
                "call": name,
                "visibility": visibility,
                "instruction_occurrences": instruction_count,
                "initial_context_occurrences": context_count,
                "priority": priority,
            }
        )

    max_priority = max((item["priority"] for item in call_evidence), default=0)
    priority_label = {
        0: "no-reference-call-difference",
        1: "latent-review",
        2: "context-visible-review",
        3: "explicit-review",
    }[max_priority]
    return {
        "task_slug": slug,
        "repository": record["repository"],
        "turn": turn,
        "run_id": record["run_id"],
        "prompt_context_classification": record["prompt_context_classification"],
        "strict_explicit_signature_subgroup": record["strict_explicit_signature_subgroup"],
        "reference_only_calls": reference_only,
        "generated_only_calls": generated_only,
        "call_evidence": call_evidence,
        "screen_priority": priority_label,
        "requires_manual_review": bool(reference_only),
        "interpretation": (
            "Candidate only: reference-only calls do not establish missed reuse; "
            "semantic equivalence, helper suitability, and context availability require manual review."
        ),
    }


def build_outputs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = read_json(METRICS_PATH)
    records = [screen_record(record) for record in source["records"]]
    if len(records) != 24:
        raise RuntimeError(f"Expected 24 eligible correct checkpoints, found {len(records)}")

    priorities = Counter(record["screen_priority"] for record in records)
    visibility = Counter(
        item["visibility"]
        for record in records
        for item in record["call_evidence"]
    )
    task_slugs = {record["task_slug"] for record in records}
    flagged = [record for record in records if record["requires_manual_review"]]
    summary = {
        "schema_version": 1,
        "method": "reference-only method-call difference, followed by manual validation",
        "scope": {
            "eligible_correct_checkpoints": len(records),
            "trajectories": len(task_slugs),
            "flagged_checkpoints": len(flagged),
            "unflagged_checkpoints": len(records) - len(flagged),
        },
        "checkpoint_priority_counts": dict(sorted(priorities.items())),
        "reference_only_call_visibility_counts": dict(sorted(visibility.items())),
        "limitations": [
            "A call difference is not proof of a missed reuse opportunity.",
            "The screen does not infer semantic equivalence between helper calls and inline code.",
            "Initial prompt context contains only code above the target function; repository helpers below it may be latent.",
            "Reference solutions can include behavior from later turns, so every candidate needs turn-aware review.",
        ],
    }
    return records, summary


def write_outputs(records: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    JSON_OUTPUT.write_text(
        json.dumps({"schema_version": 1, "records": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    columns = (
        "task_slug",
        "repository",
        "turn",
        "screen_priority",
        "requires_manual_review",
        "reference_only_calls",
        "generated_only_calls",
    )
    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            row = {key: record[key] for key in columns}
            row["reference_only_calls"] = ";".join(row["reference_only_calls"])
            row["generated_only_calls"] = ";".join(row["generated_only_calls"])
            writer.writerow(row)


def main() -> int:
    records, summary = build_outputs()
    write_outputs(records, summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
