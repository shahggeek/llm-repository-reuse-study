#!/usr/bin/env python3
"""Cumulatively test generated Pilot C checkpoints in the SR-Eval container."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import evaluate_pilot_a  # noqa: E402
import pilot_a  # noqa: E402
import pilot_c  # noqa: E402
import run_pilot_c  # noqa: E402


CONFIG_PATH = ROOT / "experiment/config/pilot-c.json"
OUTPUT_DIR = ROOT / "results/pilot/generated-tests"


class PilotCEvaluationError(RuntimeError):
    pass


def record_path(
    config: dict[str, Any], task: dict[str, Any], condition: str, repetition: int
) -> Path:
    return (
        run_pilot_c.OUTPUT_ROOT
        / run_pilot_c.run_id(config, task, condition, repetition)
        / "record.json"
    )


def validate_record(
    record: dict[str, Any],
    config: dict[str, Any],
    task: dict[str, Any],
    condition: str,
    repetition: int,
) -> None:
    expected = {
        "schema_version": 3,
        "batch_id": config["batch_id"],
        "run_id": run_pilot_c.run_id(config, task, condition, repetition),
        "repetition": repetition,
        "task_hash": task["hash_id"],
        "task_slug": task["slug"],
        "condition": condition,
        "benchmark_commit": config["benchmark_commit"],
        "prompt_source_sha256": task["prompt_source_sha256"],
    }
    for field, value in expected.items():
        if record.get(field) != value:
            raise PilotCEvaluationError(
                f"{task['slug']}/r{repetition:02d}: run record {field} mismatch"
            )
    expected_retrieval = (
        task["retrieval_sha256"] if condition == "engineering-guardrails-retrieval" else None
    )
    if record.get("retrieval_packet_sha256") != expected_retrieval:
        raise PilotCEvaluationError(
            f"{task['slug']}/r{repetition:02d}: retrieval packet digest mismatch"
        )
    if record.get("completed_at") is None:
        raise PilotCEvaluationError(f"{task['slug']}/r{repetition:02d}: generation is incomplete")
    turns = record.get("turns")
    if not isinstance(turns, list) or len(turns) != task["turns"]:
        raise PilotCEvaluationError(
            f"{task['slug']}/r{repetition:02d}: unexpected generated turn count"
        )


def evaluate_run(
    client: Any,
    config: dict[str, Any],
    task: dict[str, Any],
    condition: str,
    repetition: int,
) -> dict[str, Any]:
    path = record_path(config, task, condition, repetition)
    record = pilot_a.read_json(path)
    validate_record(record, config, task, condition, repetition)
    packet = run_pilot_c.load_packet(config, task)
    metadata = packet["metadata"]
    result: dict[str, Any] = {
        "slug": task["slug"],
        "hash_id": task["hash_id"],
        "condition": condition,
        "repetition": repetition,
        "run_id": record["run_id"],
        "checkpoints": [],
    }
    print(
        f"[{condition}/{task['slug']}/r{repetition:02d}] {task['turns']} generated checkpoints",
        flush=True,
    )
    for checkpoint_index, turn_record in enumerate(record["turns"]):
        expected_test_turns = set(range(1, checkpoint_index + 2))
        existing = {
            test["test_turn"]: test
            for test in turn_record.get("tests", [])
            if test.get("test_turn") in expected_test_turns
        }
        for test_index in range(checkpoint_index + 1):
            test_turn = test_index + 1
            if test_turn in existing:
                print(
                    f"  KEEP checkpoint {checkpoint_index + 1} vs test {test_turn}: "
                    f"{existing[test_turn]['status'].upper()}",
                    flush=True,
                )
                continue
            success, detail = client.safe_replace_and_test(
                repo=metadata["repo"],
                file_path=metadata["file_path"],
                func_start=metadata["func_start"],
                func_end=metadata["func_end"],
                new_code=turn_record["extracted_code"],
                test_file=metadata["test_file"],
                test_start=metadata["test_start"],
                test_end=metadata["test_end"],
                new_test=packet["turn_datas"][test_index]["test"],
                test_instruction=metadata["test_instruction"],
            )
            existing[test_turn] = {
                "test_turn": test_turn,
                "status": "pass" if success else "fail",
                "detail": detail,
            }
            turn_record["tests"] = [existing[number] for number in sorted(existing)]
            turn_record["cumulatively_correct"] = (
                set(existing) == expected_test_turns
                and all(item["status"] == "pass" for item in existing.values())
            )
            pilot_a.write_json(path, record)
            print(
                f"  {'PASS' if success else 'FAIL'} checkpoint {checkpoint_index + 1} "
                f"vs test {test_turn}",
                flush=True,
            )
        turn_record["tests"] = [existing[number] for number in sorted(existing)]
        turn_record["cumulatively_correct"] = (
            set(existing) == expected_test_turns
            and all(item["status"] == "pass" for item in existing.values())
        )
        result["checkpoints"].append(
            {
                "turn": checkpoint_index + 1,
                "cumulatively_correct": turn_record["cumulatively_correct"],
                "tests": turn_record["tests"],
            }
        )
        pilot_a.write_json(path, record)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--task")
    selection.add_argument("--all", action="store_true")
    parser.add_argument("--condition", required=True, choices=run_pilot_c.NEW_CONDITIONS)
    parser.add_argument("--repetition", type=int)
    parser.add_argument("--sr-eval", default=str(ROOT / ".cache/SR-Eval"))
    parser.add_argument("--container", default="mrgbench_container_1")
    args = parser.parse_args(argv)
    try:
        config = pilot_c.read_json(CONFIG_PATH)
        errors = pilot_c.validate_config(config, check_dataset=True, sr_eval=Path(args.sr_eval))
        if errors:
            raise PilotCEvaluationError("Invalid Pilot C configuration:\n- " + "\n- ".join(errors))
        JavaRepoClient = evaluate_pilot_a.load_java_client(Path(args.sr_eval).resolve())
        client = JavaRepoClient(args.container)
        started_at = dt.datetime.now(dt.timezone.utc)
        report: dict[str, Any] = {
            "schema_version": 1,
            "batch_id": config["batch_id"],
            "condition": args.condition,
            "benchmark_commit": config["benchmark_commit"],
            "container": args.container,
            "started_at": started_at.isoformat(),
            "runs": [],
        }
        tasks = run_pilot_c.selected_tasks(config, args.task, args.all)
        repetitions = run_pilot_c.selected_repetitions(config, args.repetition)
        for task in tasks:
            for repetition in repetitions:
                report["runs"].append(
                    evaluate_run(client, config, task, args.condition, repetition)
                )
        checkpoints = [
            checkpoint for run in report["runs"] for checkpoint in run["checkpoints"]
        ]
        checks = [test for checkpoint in checkpoints for test in checkpoint["tests"]]
        report["completed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        report["summary"] = {
            "runs": len(report["runs"]),
            "checkpoints": len(checkpoints),
            "cumulatively_correct_checkpoints": sum(
                checkpoint["cumulatively_correct"] for checkpoint in checkpoints
            ),
            "passed_checks": sum(test["status"] == "pass" for test in checks),
            "failed_checks": sum(test["status"] == "fail" for test in checks),
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        suffix = "all" if args.repetition is None else f"r{args.repetition:02d}"
        scope = "all" if args.all else args.task
        output = OUTPUT_DIR / f"{config['batch_id']}-{args.condition}-{scope}-{suffix}.json"
        pilot_a.write_json(output, report)
        print(f"Summary: {json.dumps(report['summary'], sort_keys=True)}", flush=True)
        print(f"Report: {output}", flush=True)
        return 0
    except (
        PilotCEvaluationError,
        evaluate_pilot_a.EvaluationError,
        pilot_a.GenerationError,
        pilot_c.PilotCError,
        run_pilot_c.PilotCRunError,
        KeyError,
        OSError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
