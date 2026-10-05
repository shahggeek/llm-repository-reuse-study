#!/usr/bin/env python3
"""Reconstruct omitted SR-Eval/MRG-Bench-derived prompts from a local checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import pilot_a  # noqa: E402
import pilot_c  # noqa: E402
import run_pilot_b  # noqa: E402
import run_pilot_c  # noqa: E402


DEFAULT_SR_EVAL = ROOT / ".cache/SR-Eval"
DEFAULT_OUTPUT = ROOT / "reconstructed-prompts"
TRAJECTORY_ROOT = ROOT / "data/generated-trajectories"


class ReconstructionError(RuntimeError):
    pass


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReconstructionError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReconstructionError(f"Expected a JSON object in {path}")
    return value


def expected_digest(turn: dict[str, Any], field: str, digest_field: str) -> str:
    stored = turn.get(digest_field)
    if isinstance(stored, str):
        return stored
    value = turn.get(field)
    if isinstance(value, str):
        return digest_text(value)
    raise ReconstructionError(f"Turn has neither {digest_field} nor textual {field}")


def task_map(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["hash_id"]: task for task in config["tasks"]}


def render_prompt(
    cohort: str,
    record: dict[str, Any],
    row: dict[str, Any],
    turn_data: dict[str, Any],
    previous_code: str,
    pilot_b_config: dict[str, Any],
    pilot_c_config: dict[str, Any],
) -> str:
    packet = {"metadata": row["metadata"], "turn_datas": row["turn_datas"]}
    condition = record["condition"]
    if cohort == "pilot-b":
        task = task_map(pilot_b_config).get(record["task_hash"])
        if task is None:
            raise ReconstructionError(f"Unknown Pilot B task hash {record['task_hash']}")
        return run_pilot_b.render_prompt(
            pilot_b_config, task, packet, condition, turn_data, previous_code
        )
    if cohort == "pilot-c":
        task = task_map(pilot_c_config).get(record["task_hash"])
        if task is None:
            raise ReconstructionError(f"Unknown Pilot C task hash {record['task_hash']}")
        return run_pilot_c.render_prompt(
            pilot_c_config, task, packet, condition, turn_data, previous_code
        )
    if cohort not in {"pilot-a", "pilot-a-amendment"}:
        raise ReconstructionError(f"Unknown trajectory cohort: {cohort}")
    protocol = read_json(ROOT / "experiment/config/protocol.json")
    template_key = "turn_1_template" if turn_data["turn_num"] == 1 else "later_turn_template"
    template = (ROOT / protocol["prompting"][template_key]).read_text(encoding="utf-8")
    return pilot_a.render_prompt(
        template,
        context=row["metadata"]["context"],
        code=previous_code,
        instruction=turn_data["instruction"],
    )


def reconstruct(sr_eval: Path, output: Path, *, verify_only: bool = False) -> int:
    protocol = read_json(ROOT / "experiment/config/protocol.json")
    expected_revision = protocol["benchmark"]["commit"]
    actual_revision = pilot_c.git_head(sr_eval)
    if actual_revision != expected_revision:
        raise ReconstructionError(
            f"SR-Eval revision mismatch: expected {expected_revision}, found {actual_revision}"
        )
    dataset = pilot_c.load_dataset(sr_eval)
    pilot_b_config = read_json(ROOT / "experiment/config/pilot-b.json")
    pilot_c_config = read_json(ROOT / "experiment/config/pilot-c.json")

    record_paths = sorted(TRAJECTORY_ROOT.glob("*/*/record.json"))
    if not record_paths:
        raise ReconstructionError("No trajectory records found")
    prompt_count = 0
    for record_path in record_paths:
        cohort = record_path.parent.parent.name
        record = read_json(record_path)
        row = dataset.get(record["task_hash"])
        if row is None:
            raise ReconstructionError(
                f"SR-Eval task {record['task_hash']} is missing for {record['run_id']}"
            )
        source_turns = row.get("turn_datas")
        recorded_turns = record.get("turns")
        if not isinstance(source_turns, list) or not isinstance(recorded_turns, list):
            raise ReconstructionError(f"Malformed turns in {record['run_id']}")
        if len(source_turns) != len(recorded_turns):
            raise ReconstructionError(f"Turn-count mismatch for {record['run_id']}")

        previous_code = ""
        for source_turn, recorded_turn in zip(source_turns, recorded_turns):
            turn_number = int(recorded_turn["turn"])
            instruction = source_turn.get("instruction")
            if not isinstance(instruction, str):
                raise ReconstructionError(
                    f"Missing benchmark instruction for {record['run_id']} turn {turn_number}"
                )
            if digest_text(instruction) != expected_digest(
                recorded_turn, "instruction", "instruction_source_sha256"
            ):
                raise ReconstructionError(
                    f"Instruction hash mismatch for {record['run_id']} turn {turn_number}"
                )
            prompt = render_prompt(
                cohort,
                record,
                row,
                source_turn,
                previous_code,
                pilot_b_config,
                pilot_c_config,
            )
            if digest_text(prompt) != expected_digest(
                recorded_turn, "prompt", "rendered_prompt_sha256"
            ):
                raise ReconstructionError(
                    f"Rendered prompt hash mismatch for {record['run_id']} turn {turn_number}"
                )
            if not verify_only:
                destination = output / cohort / record["run_id"] / f"turn-{turn_number}.prompt.txt"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(prompt, encoding="utf-8")
            previous_code = recorded_turn["extracted_code"]
            prompt_count += 1
    return prompt_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconstruct license-omitted benchmark-derived prompts and verify "
            "them against the hashes in the public run records."
        )
    )
    parser.add_argument("--sr-eval", type=Path, default=DEFAULT_SR_EVAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        count = reconstruct(
            args.sr_eval.resolve(), args.output.resolve(), verify_only=args.verify_only
        )
    except (ReconstructionError, pilot_c.PilotCError) as exc:
        print(f"Prompt reconstruction failed: {exc}", file=sys.stderr)
        return 1
    action = "Verified" if args.verify_only else "Reconstructed and verified"
    print(f"{action} {count} prompts against the pinned SR-Eval checkout")
    if not args.verify_only:
        print(f"Output: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
