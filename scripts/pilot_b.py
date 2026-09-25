#!/usr/bin/env python3
"""Validate the frozen Pilot B mechanism-probe configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "experiment/config/pilot-b.json"
DEFAULT_SR_EVAL = ROOT / ".cache/SR-Eval"

EXPECTED_CONDITIONS = [
    "baseline",
    "engineering-guardrails",
    "engineering-guardrails-retrieval",
]
EXPECTED_TASKS = {
    "loadDocuments": "6712ca73ea1cb5649aa72a63",
    "addInOrder": "892c3ff660b30a2824182053",
    "ensureCapacity": "b4e1056e5ea2a627db586be4",
    "nodeArrayMerge": "29066589401870d85f4e87b3",
    "randomAccessScoreProvider": "a3045dd878c9235e7d26de84",
    "diff": "dcb5dab97ac7ba282aeed44a",
}


class PilotBError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PilotBError(f"Cannot read JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotBError(f"Expected a JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise PilotBError(f"Cannot hash {path}: {exc}") from exc


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


def check_hashed_file(spec: Any, label: str, errors: list[str]) -> None:
    if not isinstance(spec, dict):
        errors.append(f"{label}: expected path/sha256 object")
        return
    path = resolve_local(spec.get("path"), label, errors)
    expected = spec.get("sha256")
    if not isinstance(expected, str) or len(expected) != 64:
        errors.append(f"{label}: sha256 must be a 64-character digest")
    elif path is not None and sha256(path) != expected:
        errors.append(f"{label}: SHA-256 mismatch")


def validate_config(config: dict[str, Any], check_dataset: bool = False, sr_eval: Path = DEFAULT_SR_EVAL) -> list[str]:
    errors: list[str] = []
    if config.get("status") != "pilot-b-frozen":
        errors.append("status must be 'pilot-b-frozen'")
    if config.get("revision") != 2:
        errors.append("revision must be 2")
    if config.get("runs_per_task_new_condition") != 1:
        errors.append("runs_per_task_new_condition must be 1")

    base_protocol = ROOT / "experiment/config/protocol.json"
    if config.get("base_protocol_sha256") != sha256(base_protocol):
        errors.append("base_protocol_sha256 does not match the frozen Pilot A protocol")

    check_hashed_file(config.get("run_record_schema"), "run_record_schema", errors)
    prompting = config.get("prompting")
    if not isinstance(prompting, dict):
        errors.append("prompting must be an object")
    else:
        for name in ("system_prompt", "turn_1_template", "later_turn_template", "guardrails", "retrieval_header"):
            check_hashed_file(prompting.get(name), f"prompting.{name}", errors)

    conditions = config.get("conditions")
    names = [item.get("name") for item in conditions if isinstance(item, dict)] if isinstance(conditions, list) else []
    if names != EXPECTED_CONDITIONS:
        errors.append(f"conditions must be exactly {EXPECTED_CONDITIONS}")
    if isinstance(conditions, list) and len(conditions) == 3:
        if conditions[0].get("new_generation") is not False:
            errors.append("baseline must reuse the existing Pilot A generation")
        for item in conditions[1:]:
            if item.get("new_generation") is not True or item.get("guardrails") is not True:
                errors.append(f"{item.get('name')}: must be a new guardrail generation")
        if conditions[1].get("retrieval_packet") is not False:
            errors.append("engineering-guardrails must not receive a retrieval packet")
        if conditions[2].get("retrieval_packet") is not True:
            errors.append("engineering-guardrails-retrieval must receive a retrieval packet")

    policy = config.get("retrieval_policy")
    max_chars = policy.get("maximum_packet_characters") if isinstance(policy, dict) else None
    max_symbols = policy.get("maximum_symbols_per_task") if isinstance(policy, dict) else None
    if not isinstance(max_chars, int) or max_chars <= 0:
        errors.append("retrieval_policy.maximum_packet_characters must be positive")
        max_chars = 0
    if max_symbols != 4:
        errors.append("retrieval_policy.maximum_symbols_per_task must remain 4")

    tasks = config.get("tasks")
    if not isinstance(tasks, list):
        return errors + ["tasks must be an array"]
    slugs = [task.get("slug") for task in tasks if isinstance(task, dict)]
    if set(slugs) != set(EXPECTED_TASKS) or len(slugs) != len(EXPECTED_TASKS):
        errors.append("tasks must contain the six predeclared Pilot B cases exactly once")

    for task in tasks:
        if not isinstance(task, dict):
            errors.append("each task must be an object")
            continue
        slug = task.get("slug")
        label = f"task {slug!r}"
        if EXPECTED_TASKS.get(slug) != task.get("hash_id"):
            errors.append(f"{label}: unexpected benchmark hash")
        signature = task.get("target_signature")
        function = task.get("function")
        if not isinstance(signature, str) or not isinstance(function, str) or f"{function}(" not in signature:
            errors.append(f"{label}: literal repository-compatible target signature is required")
        if not isinstance(task.get("baseline_run_id"), str) or not task["baseline_run_id"]:
            errors.append(f"{label}: baseline_run_id is required")
        if task.get("packet_source") not in {"pilot-a", "pilot-a-amendment"}:
            errors.append(f"{label}: packet_source is invalid")
        source_digest = task.get("prompt_source_sha256")
        if not isinstance(source_digest, str) or len(source_digest) != 64:
            errors.append(f"{label}: prompt_source_sha256 must be a SHA-256 digest")
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
                    errors.append(f"{label}: retrieval packet contains forbidden benchmark material {forbidden!r}")

    if check_dataset:
        dataset = sr_eval / "dataset/java_repository.jsonl"
        try:
            rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"cannot read pinned SR-Eval dataset: {exc}")
        else:
            index = {row.get("hash_id"): row for row in rows}
            for task in tasks:
                if not isinstance(task, dict):
                    continue
                row = index.get(task.get("hash_id"))
                if row is None:
                    errors.append(f"task {task.get('slug')!r}: hash missing from SR-Eval dataset")
                    continue
                metadata = row.get("metadata", {})
                expected = (task.get("repo"), task.get("function"), task.get("turns"))
                actual = (metadata.get("repo"), metadata.get("func_name"), row.get("total_turn"))
                if actual != expected:
                    errors.append(f"task {task.get('slug')!r}: SR-Eval metadata mismatch")
                turn_data = row.get("turn_datas")
                if not isinstance(metadata.get("context"), str) or not isinstance(turn_data, list):
                    errors.append(f"task {task.get('slug')!r}: malformed prompt source")
                    continue
                instructions = [turn.get("instruction") for turn in turn_data if isinstance(turn, dict)]
                if len(instructions) != task.get("turns") or any(
                    not isinstance(instruction, str) for instruction in instructions
                ):
                    errors.append(f"task {task.get('slug')!r}: malformed turn instructions")
                    continue
                actual_digest = prompt_source_sha256(metadata["context"], instructions)
                if actual_digest != task.get("prompt_source_sha256"):
                    errors.append(f"task {task.get('slug')!r}: prompt source SHA-256 mismatch")
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
    except PilotBError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    new_runs = len(config["tasks"]) * sum(condition["new_generation"] for condition in config["conditions"])
    print(
        f"Pilot B frozen and valid: {len(config['tasks'])} tasks, "
        f"3 conditions, {new_runs} new trajectories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
