#!/usr/bin/env python3
"""Cumulatively test generated Pilot A checkpoints in the SR-Eval container."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "experiment/config/protocol.json"
MANIFEST_PATH = ROOT / "experiment/config/pilot-tasks.json"
PACKET_DIR = ROOT / "work/task-packets"
OUTPUT_DIR = ROOT / "results/pilot/generated-tests"


class EvaluationError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def run_record_path(protocol: dict[str, Any], task: dict[str, Any]) -> Path:
    batch_id = protocol["pilot_a"]["batch_id"]
    run_id = f"{batch_id}-{task['slug']}-01"
    return ROOT / "data/generated-trajectories/pilot-a" / run_id / "record.json"


def validate_record(record: dict[str, Any], protocol: dict[str, Any], task: dict[str, Any]) -> None:
    if record.get("task_hash") != task["hash_id"]:
        raise EvaluationError(f"Run record hash mismatch for {task['slug']}")
    if record.get("benchmark_commit") != protocol["benchmark"]["commit"]:
        raise EvaluationError(f"Run record benchmark mismatch for {task['slug']}")
    if record.get("completed_at") is None:
        raise EvaluationError(f"Generation is incomplete for {task['slug']}")
    turns = record.get("turns")
    if not isinstance(turns, list) or len(turns) != task["turns"]:
        raise EvaluationError(f"Unexpected turn count for {task['slug']}")


def load_java_client(sr_eval: Path) -> Any:
    module_path = sr_eval / "data_construction/data/seed/mrgbench/java_repo_client.py"
    spec = importlib.util.spec_from_file_location("sr_eval_java_repo_client", module_path)
    if spec is None or spec.loader is None:
        raise EvaluationError(f"Cannot load module specification from {module_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise EvaluationError(f"Cannot import SR-Eval JavaRepoClient: {exc}") from exc
    return module.JavaRepoClient


def selected_tasks(manifest: dict[str, Any], slug: str | None, all_tasks: bool) -> list[dict[str, Any]]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise EvaluationError("Manifest tasks must be an array")
    if all_tasks:
        return tasks
    matches = [task for task in tasks if task.get("slug") == slug]
    if not matches:
        raise EvaluationError(f"Unknown Pilot A task: {slug}")
    return matches


def evaluate_task(
    client: Any,
    protocol: dict[str, Any],
    task: dict[str, Any],
) -> dict[str, Any]:
    record_path = run_record_path(protocol, task)
    record = read_json(record_path)
    validate_record(record, protocol, task)
    packet = read_json(PACKET_DIR / f"{task['slug']}.json")
    metadata = packet["metadata"]
    task_result: dict[str, Any] = {
        "slug": task["slug"],
        "hash_id": task["hash_id"],
        "checkpoints": [],
    }

    print(f"[{task['slug']}] {task['turns']} generated checkpoints", flush=True)
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
            result = {
                "test_turn": test_turn,
                "status": "pass" if success else "fail",
                "detail": detail,
            }
            existing[test_turn] = result
            turn_record["tests"] = [existing[number] for number in sorted(existing)]
            turn_record["cumulatively_correct"] = (
                set(existing) == expected_test_turns
                and all(item["status"] == "pass" for item in existing.values())
            )
            write_json(record_path, record)
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
        task_result["checkpoints"].append(
            {
                "turn": checkpoint_index + 1,
                "cumulatively_correct": turn_record["cumulatively_correct"],
                "tests": turn_record["tests"],
            }
        )
        write_json(record_path, record)
    return task_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--task")
    choice.add_argument("--all", action="store_true")
    parser.add_argument("--sr-eval", default=str(ROOT / ".cache/SR-Eval"))
    parser.add_argument("--container", default="mrgbench_container_1")
    args = parser.parse_args(argv)

    try:
        protocol = read_json(PROTOCOL_PATH)
        manifest = read_json(MANIFEST_PATH)
        sr_eval = Path(args.sr_eval).resolve()
        if manifest.get("benchmark_commit") != protocol["benchmark"]["commit"]:
            raise EvaluationError("Manifest and protocol benchmark revisions differ")
        JavaRepoClient = load_java_client(sr_eval)
        client = JavaRepoClient(args.container)
        started_at = dt.datetime.now(dt.timezone.utc)
        report: dict[str, Any] = {
            "schema_version": 1,
            "batch_id": protocol["pilot_a"]["batch_id"],
            "benchmark_commit": protocol["benchmark"]["commit"],
            "container": args.container,
            "started_at": started_at.isoformat(),
            "tasks": [],
        }
        for task in selected_tasks(manifest, args.task, args.all):
            report["tasks"].append(evaluate_task(client, protocol, task))

        checkpoints = [
            checkpoint
            for task_result in report["tasks"]
            for checkpoint in task_result["checkpoints"]
        ]
        checks = [test for checkpoint in checkpoints for test in checkpoint["tests"]]
        report["completed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        report["summary"] = {
            "tasks": len(report["tasks"]),
            "checkpoints": len(checkpoints),
            "cumulatively_correct_checkpoints": sum(
                checkpoint["cumulatively_correct"] for checkpoint in checkpoints
            ),
            "passed_checks": sum(test["status"] == "pass" for test in checks),
            "failed_checks": sum(test["status"] == "fail" for test in checks),
        }
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{protocol['pilot_a']['batch_id']}.json"
        write_json(output_path, report)
        print(f"Summary: {json.dumps(report['summary'], sort_keys=True)}", flush=True)
        print(f"Report: {output_path}", flush=True)
        return 0
    except (EvaluationError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
