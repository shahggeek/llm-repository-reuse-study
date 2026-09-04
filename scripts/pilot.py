#!/usr/bin/env python3
"""Validate, export, and smoke-test the frozen SR-Eval Java pilot."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "experiment/config/pilot-tasks.json"
DEFAULT_PROTOCOL = ROOT / "experiment/config/protocol.json"
DEFAULT_EXPORT = ROOT / "work/task-packets"
DEFAULT_RESULTS = ROOT / "results/pilot/smoke-tests"


class PilotError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotError(f"Cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotError(f"Expected a JSON object in {path}")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise PilotError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
                if not isinstance(value, dict):
                    raise PilotError(f"Expected an object at {path}:{line_number}")
                rows.append(value)
    except OSError as exc:
        raise PilotError(f"Cannot read dataset {path}: {exc}") from exc
    return rows


def manifest_tasks(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise PilotError("Manifest field 'tasks' must be an array")
    return tasks


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        return ["tasks must be an array"]
    if len(tasks) != 18:
        errors.append(f"expected 18 tasks, found {len(tasks)}")

    required = {"slug", "hash_id", "repo", "function", "turns", "stratum", "pilot_b", "rationale"}
    slugs: set[str] = set()
    hashes: set[str] = set()
    for index, task in enumerate(tasks, 1):
        if not isinstance(task, dict):
            errors.append(f"task {index} is not an object")
            continue
        missing = sorted(required - task.keys())
        if missing:
            errors.append(f"task {index} missing: {', '.join(missing)}")
            continue
        slug = task["slug"]
        hash_id = task["hash_id"]
        if slug in slugs:
            errors.append(f"duplicate slug: {slug}")
        if hash_id in hashes:
            errors.append(f"duplicate hash_id: {hash_id}")
        slugs.add(slug)
        hashes.add(hash_id)
        if task["stratum"] not in {"primary", "control"}:
            errors.append(f"{slug}: invalid stratum {task['stratum']!r}")
        if not isinstance(task["pilot_b"], bool):
            errors.append(f"{slug}: pilot_b must be boolean")
        if not isinstance(task["turns"], int) or not 2 <= task["turns"] <= 5:
            errors.append(f"{slug}: turns must be an integer from 2 to 5")

    primary = sum(task.get("stratum") == "primary" for task in tasks if isinstance(task, dict))
    controls = sum(task.get("stratum") == "control" for task in tasks if isinstance(task, dict))
    paired = sum(task.get("pilot_b") is True for task in tasks if isinstance(task, dict))
    if primary != 12 or controls != 6:
        errors.append(f"expected 12 primary and 6 control tasks, found {primary} and {controls}")
    if paired != 6:
        errors.append(f"expected 6 Pilot B tasks, found {paired}")
    return errors


def dataset_index(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        hash_id = row.get("hash_id")
        if isinstance(hash_id, str):
            if hash_id in result:
                raise PilotError(f"Duplicate dataset hash_id: {hash_id}")
            result[hash_id] = row
    return result


def match_tasks(
    manifest: dict[str, Any], rows: Iterable[dict[str, Any]]
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[str]]:
    index = dataset_index(rows)
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    errors: list[str] = []
    for task in manifest_tasks(manifest):
        row = index.get(task["hash_id"])
        if row is None:
            errors.append(f"{task['slug']}: hash {task['hash_id']} not found")
            continue
        metadata = row.get("metadata", {})
        checks = {
            "repo": metadata.get("repo"),
            "function": metadata.get("func_name"),
            "turns": row.get("total_turn"),
        }
        for field, actual in checks.items():
            if task[field] != actual:
                errors.append(
                    f"{task['slug']}: {field} expected {task[field]!r}, dataset has {actual!r}"
                )
        turn_data = row.get("turn_datas")
        if not isinstance(turn_data, list) or len(turn_data) != task["turns"]:
            errors.append(f"{task['slug']}: malformed turn_datas")
        elif any(not turn.get("solution") or not turn.get("test") for turn in turn_data):
            errors.append(f"{task['slug']}: a reference solution or test is empty")
        matches.append((task, row))
    return matches, errors


def git_head(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise PilotError(f"Cannot resolve Git revision in {repo}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def prompt_hashes(protocol: dict[str, Any]) -> dict[str, str]:
    prompt_config = protocol.get("prompting", {})
    hashes: dict[str, str] = {}
    for name in ("system_prompt", "turn_1_template", "later_turn_template", "guardrails"):
        relative = prompt_config.get(name)
        if not isinstance(relative, str):
            raise PilotError(f"Protocol prompt path missing: {name}")
        path = ROOT / relative
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise PilotError(f"Cannot read prompt {path}: {exc}") from exc
        hashes[relative] = hashlib.sha256(content).hexdigest()
    return hashes


def selected_matches(args: argparse.Namespace) -> tuple[dict[str, Any], list[tuple[dict[str, Any], dict[str, Any]]]]:
    manifest = read_json(Path(args.manifest))
    manifest_errors = validate_manifest(manifest)
    if manifest_errors:
        raise PilotError("Invalid manifest:\n- " + "\n- ".join(manifest_errors))
    sr_eval = Path(args.sr_eval).resolve()
    expected = manifest.get("benchmark_commit")
    actual = git_head(sr_eval)
    if actual != expected:
        raise PilotError(f"SR-Eval revision mismatch: expected {expected}, found {actual}")
    rows = read_jsonl(sr_eval / "dataset/java_repository.jsonl")
    matches, errors = match_tasks(manifest, rows)
    if errors:
        raise PilotError("Dataset mismatch:\n- " + "\n- ".join(errors))
    return manifest, matches


def choose_matches(
    matches: list[tuple[dict[str, Any], dict[str, Any]]], task_slug: str | None, all_tasks: bool
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    if all_tasks:
        return matches
    if not task_slug:
        raise PilotError("Choose --task SLUG or --all")
    chosen = [match for match in matches if match[0]["slug"] == task_slug]
    if not chosen:
        available = ", ".join(task["slug"] for task, _ in matches)
        raise PilotError(f"Unknown task {task_slug!r}. Available: {available}")
    return chosen


def command_validate_manifest(args: argparse.Namespace) -> int:
    manifest = read_json(Path(args.manifest))
    errors = validate_manifest(manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    protocol = read_json(DEFAULT_PROTOCOL)
    hashes = prompt_hashes(protocol)
    print("Manifest valid: 18 tasks (12 primary, 6 controls, 6 Pilot B pairs)")
    print("Prompt SHA-256:")
    for path, digest in sorted(hashes.items()):
        print(f"  {digest}  {path}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    _, matches = selected_matches(args)
    print(f"Validated {len(matches)} tasks against {Path(args.sr_eval).resolve()}")
    print(f"{'slug':30} {'repo':18} {'turns':>5} {'group':8} pilot-b")
    for task, _ in matches:
        marker = "yes" if task["pilot_b"] else "no"
        print(f"{task['slug']:30} {task['repo']:18} {task['turns']:>5} {task['stratum']:8} {marker}")
    return 0


def command_export(args: argparse.Namespace) -> int:
    _, matches = selected_matches(args)
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for task, row in matches:
        packet = {
            "study_task": task,
            "benchmark": {
                "name": "SR-Eval",
                "commit": git_head(Path(args.sr_eval).resolve()),
                "hash_id": row["hash_id"],
            },
            "metadata": row["metadata"],
            "turn_datas": row["turn_datas"],
        }
        path = output / f"{task['slug']}.json"
        path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Exported {len(matches)} task packets to {output}")
    return 0


def command_doctor(args: argparse.Namespace) -> int:
    failed = False
    for tool in ("git", "docker", "uv", "python3"):
        found = shutil.which(tool)
        print(f"{tool:8} {'OK ' + found if found else 'MISSING'}")
        failed = failed or found is None
    lfs = subprocess.run(["git", "lfs", "version"], text=True, capture_output=True, check=False)
    print(f"git-lfs  {'OK ' + lfs.stdout.strip() if lfs.returncode == 0 else 'MISSING'}")
    failed = failed or lfs.returncode != 0

    sr_eval = Path(args.sr_eval).resolve()
    try:
        actual = git_head(sr_eval)
        expected = read_json(DEFAULT_PROTOCOL)["benchmark"]["commit"]
        status = "OK" if actual == expected else f"WRONG REVISION ({actual})"
        print(f"SR-Eval  {status}")
        failed = failed or actual != expected
    except PilotError as exc:
        print(f"SR-Eval  MISSING ({exc})")
        failed = True

    docker_info = subprocess.run(["docker", "info"], text=True, capture_output=True, check=False)
    print(f"daemon   {'OK' if docker_info.returncode == 0 else 'UNAVAILABLE'}")
    failed = failed or docker_info.returncode != 0
    container = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", args.container],
        text=True,
        capture_output=True,
        check=False,
    )
    running = container.returncode == 0 and container.stdout.strip() == "true"
    print(f"container {'OK ' + args.container if running else 'NOT RUNNING ' + args.container}")
    failed = failed or not running
    return 1 if failed else 0


def smoke_plan(task: dict[str, Any], row: dict[str, Any]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for checkpoint_index, checkpoint in enumerate(row["turn_datas"]):
        for test_index in range(checkpoint_index + 1):
            plan.append(
                {
                    "task": task["slug"],
                    "checkpoint_turn": checkpoint_index + 1,
                    "test_turn": test_index + 1,
                    "repo": row["metadata"]["repo"],
                    "test_instruction": row["metadata"]["test_instruction"],
                    "solution": checkpoint["solution"],
                    "test": row["turn_datas"][test_index]["test"],
                }
            )
    return plan


def run_smoke_item(client: Any, row: dict[str, Any], item: dict[str, Any]) -> tuple[bool, str]:
    metadata = row["metadata"]
    return client.safe_replace_and_test(
        repo=metadata["repo"],
        file_path=metadata["file_path"],
        func_start=metadata["func_start"],
        func_end=metadata["func_end"],
        new_code=item["solution"],
        test_file=metadata["test_file"],
        test_start=metadata["test_start"],
        test_end=metadata["test_end"],
        new_test=item["test"],
        test_instruction=metadata["test_instruction"],
    )


def command_smoke_test(args: argparse.Namespace) -> int:
    _, matches = selected_matches(args)
    chosen = choose_matches(matches, args.task, args.all)
    plans = [(task, row, smoke_plan(task, row)) for task, row in chosen]

    if args.dry_run:
        for task, _, plan in plans:
            print(f"{task['slug']}: {task['turns']} checkpoints, {len(plan)} cumulative test executions")
            for item in plan:
                print(
                    f"  checkpoint {item['checkpoint_turn']} vs test {item['test_turn']}: "
                    f"{item['test_instruction']}"
                )
        return 0

    sr_eval = Path(args.sr_eval).resolve()
    sys.path.insert(0, str(sr_eval))
    try:
        from data_construction.data.seed.mrgbench.java_repo_client import JavaRepoClient
    except Exception as exc:
        raise PilotError(
            "Cannot import SR-Eval JavaRepoClient. Run through the pinned SR-Eval uv environment: "
            "uv run --project .cache/SR-Eval python scripts/pilot.py smoke-test ..."
        ) from exc

    client = JavaRepoClient(args.container)
    started = dt.datetime.now(dt.timezone.utc)
    report: dict[str, Any] = {
        "schema_version": 1,
        "benchmark_commit": git_head(sr_eval),
        "container": args.container,
        "started_at": started.isoformat(),
        "tasks": [],
    }
    all_pass = True
    for task, row, plan in plans:
        task_report: dict[str, Any] = {
            "slug": task["slug"],
            "hash_id": task["hash_id"],
            "checks": [],
        }
        print(f"[{task['slug']}] {len(plan)} cumulative test executions")
        for item in plan:
            success, detail = run_smoke_item(client, row, item)
            all_pass = all_pass and success
            status = "PASS" if success else "FAIL"
            print(f"  {status} checkpoint {item['checkpoint_turn']} vs test {item['test_turn']}")
            task_report["checks"].append(
                {
                    "checkpoint_turn": item["checkpoint_turn"],
                    "test_turn": item["test_turn"],
                    "status": "pass" if success else "fail",
                    "detail": detail,
                }
            )
            if not success and args.fail_fast:
                break
        report["tasks"].append(task_report)
        if not all_pass and args.fail_fast:
            break

    report["completed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    report["status"] = "pass" if all_pass else "fail"
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"reference-smoke-{stamp}.json"
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {output_path}")
    return 0 if all_pass else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(func=None)
    subparsers = parser.add_subparsers(dest="command")

    manifest_parser = subparsers.add_parser("validate-manifest", help="validate frozen local configuration")
    manifest_parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    manifest_parser.set_defaults(func=command_validate_manifest)

    def add_dataset_options(child: argparse.ArgumentParser) -> None:
        child.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
        child.add_argument("--sr-eval", default=str(ROOT / ".cache/SR-Eval"))

    validate_parser = subparsers.add_parser("validate", help="match selected tasks to the pinned dataset")
    add_dataset_options(validate_parser)
    validate_parser.set_defaults(func=command_validate)

    export_parser = subparsers.add_parser("export", help="export selected benchmark task packets locally")
    add_dataset_options(export_parser)
    export_parser.add_argument("--output", default=str(DEFAULT_EXPORT))
    export_parser.set_defaults(func=command_export)

    doctor_parser = subparsers.add_parser("doctor", help="check local smoke-test prerequisites")
    doctor_parser.add_argument("--sr-eval", default=str(ROOT / ".cache/SR-Eval"))
    doctor_parser.add_argument("--container", default="mrgbench_container_1")
    doctor_parser.set_defaults(func=command_doctor)

    smoke_parser = subparsers.add_parser("smoke-test", help="test reference trajectories cumulatively")
    add_dataset_options(smoke_parser)
    choice = smoke_parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--task", help="one task slug")
    choice.add_argument("--all", action="store_true", help="all 18 tasks")
    smoke_parser.add_argument("--container", default="mrgbench_container_1")
    smoke_parser.add_argument("--output", default=str(DEFAULT_RESULTS))
    smoke_parser.add_argument("--dry-run", action="store_true")
    smoke_parser.add_argument("--fail-fast", action="store_true")
    smoke_parser.set_defaults(func=command_smoke_test)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.func is None:
        parser.print_help()
        return 2
    try:
        return int(args.func(args))
    except PilotError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
