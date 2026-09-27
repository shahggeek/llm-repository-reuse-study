#!/usr/bin/env python3
"""Validate the frozen Pilot C cross-repository replication configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "experiment/config/pilot-c.json"
DEFAULT_SR_EVAL = ROOT / ".cache/SR-Eval"
EXPECTED_CONDITIONS = ["engineering-guardrails", "engineering-guardrails-retrieval"]
EXPECTED_TASKS = {
    "loadDocumentsRecursively": "3ac2084e8f23beb3709c38d6",
    "merge": "0fa49588ebdc16e8fd289f95",
}


class PilotCError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotCError(f"Cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotCError(f"Expected a JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PilotCError(f"Cannot hash {path}: {exc}") from exc


def prompt_source_sha256(context: str, instructions: list[str]) -> str:
    payload = {"context": context, "instructions": instructions}
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def resolve_local(relative: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{label}: path must be a non-empty string")
        return None
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"{label}: path escapes the repository")
        return None
    if not path.is_file():
        errors.append(f"{label}: file does not exist: {relative}")
        return None
    return path


def check_hashed_file(spec: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(spec, dict):
        errors.append(f"{label}: expected path/sha256 object")
        return None
    path = resolve_local(spec.get("path"), label, errors)
    expected = spec.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        errors.append(f"{label}: sha256 must be a 64-character digest")
    elif path is not None and sha256(path) != expected:
        errors.append(f"{label}: SHA-256 mismatch")
    return path


def git_head(path: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise PilotCError(f"Cannot resolve benchmark revision: {completed.stderr.strip()}")
    return completed.stdout.strip()


def load_dataset(sr_eval: Path) -> dict[str, dict[str, Any]]:
    path = sr_eval / "dataset/java_repository.jsonl"
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotCError(f"Cannot read pinned SR-Eval dataset: {exc}") from exc
    return {row["hash_id"]: row for row in rows}


def validate_config(
    config: dict[str, Any], check_dataset: bool = False, sr_eval: Path = DEFAULT_SR_EVAL
) -> list[str]:
    errors: list[str] = []
    if config.get("status") != "pilot-c-frozen":
        errors.append("status must be 'pilot-c-frozen'")
    if config.get("revision") != 1:
        errors.append("revision must be 1")
    if config.get("selection_frozen_before_model_contact") is not True:
        errors.append("selection must be frozen before model contact")
    repetitions = config.get("runs_per_task_condition")
    if repetitions != 3:
        errors.append("runs_per_task_condition must be 3")
    if config.get("planned_trajectories") != 12:
        errors.append("planned_trajectories must be 12")

    base_protocol = ROOT / "experiment/config/protocol.json"
    if config.get("base_protocol_sha256") != sha256(base_protocol):
        errors.append("base_protocol_sha256 does not match the frozen Pilot A protocol")
    check_hashed_file(config.get("reference_smoke"), "reference_smoke", errors)
    check_hashed_file(config.get("run_record_schema"), "run_record_schema", errors)

    prompting = config.get("prompting")
    if not isinstance(prompting, dict):
        errors.append("prompting must be an object")
    else:
        for name in (
            "system_prompt",
            "turn_1_template",
            "later_turn_template",
            "guardrails",
            "retrieval_header",
        ):
            check_hashed_file(prompting.get(name), f"prompting.{name}", errors)

    conditions = config.get("conditions")
    names = (
        [item.get("name") for item in conditions if isinstance(item, dict)]
        if isinstance(conditions, list)
        else []
    )
    if names != EXPECTED_CONDITIONS:
        errors.append(f"conditions must be exactly {EXPECTED_CONDITIONS}")
    elif (
        conditions[0].get("retrieval_packet") is not False
        or conditions[1].get("retrieval_packet") is not True
        or any(item.get("new_generation") is not True for item in conditions)
        or any(item.get("guardrails") is not True for item in conditions)
    ):
        errors.append("condition treatment flags are invalid")

    policy = config.get("retrieval_policy")
    max_chars = policy.get("maximum_packet_characters") if isinstance(policy, dict) else 0
    max_symbols = policy.get("maximum_symbols_per_task") if isinstance(policy, dict) else None
    if not isinstance(max_chars, int) or max_chars <= 0:
        errors.append("retrieval_policy.maximum_packet_characters must be positive")
        max_chars = 0
    if max_symbols != 4:
        errors.append("retrieval_policy.maximum_symbols_per_task must be 4")

    tasks = config.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["tasks must be an array"]
    slugs = [task.get("slug") for task in tasks if isinstance(task, dict)]
    if set(slugs) != set(EXPECTED_TASKS) or len(slugs) != len(EXPECTED_TASKS):
        errors.append("tasks must contain the two predeclared Pilot C cases exactly once")
    repos = {task.get("repo") for task in tasks if isinstance(task, dict)}
    if len(repos) != 2 or "jvector" in repos:
        errors.append("tasks must span two distinct non-JVector repositories")

    dataset_index: dict[str, dict[str, Any]] = {}
    if check_dataset:
        try:
            if git_head(sr_eval) != config.get("benchmark_commit"):
                errors.append("pinned SR-Eval revision mismatch")
            dataset_index = load_dataset(sr_eval)
        except PilotCError as exc:
            errors.append(str(exc))

    for task in tasks:
        if not isinstance(task, dict):
            errors.append("each task must be an object")
            continue
        slug = task.get("slug")
        label = f"task {slug!r}"
        if EXPECTED_TASKS.get(slug) != task.get("hash_id"):
            errors.append(f"{label}: unexpected benchmark hash")
        symbols = task.get("retrieval_symbols")
        if not isinstance(symbols, list) or not symbols or len(symbols) > 4:
            errors.append(f"{label}: retrieval_symbols must contain 1-4 entries")
        signature = task.get("target_signature")
        function = task.get("function")
        if not isinstance(signature, str) or not isinstance(function, str) or f"{function}(" not in signature:
            errors.append(f"{label}: literal target signature is required")
        packet = resolve_local(task.get("retrieval_packet"), f"{label} retrieval packet", errors)
        digest = task.get("retrieval_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"{label}: retrieval_sha256 must be a SHA-256 digest")
        elif packet is not None and sha256(packet) != digest:
            errors.append(f"{label}: retrieval packet SHA-256 mismatch")
        if packet is not None:
            text = packet.read_text(encoding="utf-8")
            if max_chars and len(text) > max_chars:
                errors.append(f"{label}: retrieval packet exceeds {max_chars} characters")
            for forbidden in ("TURN 1", "SOLUTION:", "@Test", "assertThat("):
                if forbidden in text:
                    errors.append(f"{label}: packet contains forbidden material {forbidden!r}")

        if check_dataset and dataset_index:
            row = dataset_index.get(task.get("hash_id"))
            if row is None:
                errors.append(f"{label}: hash missing from SR-Eval dataset")
                continue
            metadata = row.get("metadata", {})
            actual = (metadata.get("repo"), metadata.get("func_name"), row.get("total_turn"))
            expected = (task.get("repo"), task.get("function"), task.get("turns"))
            if actual != expected:
                errors.append(f"{label}: SR-Eval metadata mismatch")
            turns = row.get("turn_datas")
            if not isinstance(turns, list) or not isinstance(metadata.get("context"), str):
                errors.append(f"{label}: malformed prompt source")
                continue
            instructions = [turn.get("instruction") for turn in turns if isinstance(turn, dict)]
            if task.get("target_signature") not in instructions[0]:
                errors.append(f"{label}: turn-1 instruction lacks the frozen signature")
            actual_digest = prompt_source_sha256(metadata["context"], instructions)
            if actual_digest != task.get("prompt_source_sha256"):
                errors.append(f"{label}: prompt source SHA-256 mismatch")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--check-dataset", action="store_true")
    parser.add_argument("--sr-eval", default=str(DEFAULT_SR_EVAL))
    args = parser.parse_args(argv)
    try:
        config = read_json(Path(args.config))
        errors = validate_config(config, args.check_dataset, Path(args.sr_eval))
    except PilotCError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Pilot C frozen and valid: 2 repositories, 2 conditions, 3 repetitions, 12 trajectories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
