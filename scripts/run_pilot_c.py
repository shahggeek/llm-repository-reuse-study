#!/usr/bin/env python3
"""Render, preflight, and run the frozen Pilot C replication trajectories."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import pilot_a  # noqa: E402
import pilot_c  # noqa: E402


CONFIG_PATH = ROOT / "experiment/config/pilot-c.json"
OUTPUT_ROOT = ROOT / "data/generated-trajectories/pilot-c"
SESSION_ROOT = ROOT / "work/pilot-c-sessions"
PREFLIGHT_ROOT = ROOT / "work/pilot-c-preflight"
PREFLIGHT_SUMMARY = ROOT / "results/pilot/pilot-c-preflight-summary.json"
DEFAULT_CODEX = ROOT / ".tools/codex-cli-0.153.0/node_modules/.bin/codex"
NEW_CONDITIONS = ("engineering-guardrails", "engineering-guardrails-retrieval")
PREVIOUS_CODE_SENTINEL = "/* PREVIOUS GENERATED METHOD: supplied only during the actual resumed run */"


class PilotCRunError(RuntimeError):
    pass


def read_text_spec(spec: dict[str, Any]) -> str:
    path = ROOT / spec["path"]
    if pilot_c.sha256(path) != spec["sha256"]:
        raise PilotCRunError(f"Frozen file hash mismatch: {spec['path']}")
    return path.read_text(encoding="utf-8")


def runtime_protocol(config: dict[str, Any]) -> dict[str, Any]:
    prompting = config["prompting"]
    return {
        "model": config["model"],
        "execution": config["execution"],
        "prompting": {
            "system_prompt": prompting["system_prompt"]["path"],
            "turn_1_template": prompting["turn_1_template"]["path"],
            "later_turn_template": prompting["later_turn_template"]["path"],
            "guardrails": prompting["guardrails"]["path"],
        },
    }


def dataset_index(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index = pilot_c.load_dataset(ROOT / ".cache/SR-Eval")
    if pilot_c.git_head(ROOT / ".cache/SR-Eval") != config["benchmark_commit"]:
        raise PilotCRunError("Pinned SR-Eval revision mismatch")
    return index


def load_packet(config: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    row = dataset_index(config).get(task["hash_id"])
    if row is None:
        raise PilotCRunError(f"Dataset task missing for {task['slug']}")
    turns = row.get("turn_datas")
    metadata = row.get("metadata")
    if not isinstance(turns, list) or len(turns) != task["turns"] or not isinstance(metadata, dict):
        raise PilotCRunError(f"Malformed task packet for {task['slug']}")
    instructions = [turn.get("instruction") for turn in turns if isinstance(turn, dict)]
    context = metadata.get("context")
    if (
        len(instructions) != task["turns"]
        or any(not isinstance(item, str) for item in instructions)
        or not isinstance(context, str)
    ):
        raise PilotCRunError(f"Malformed prompt source for {task['slug']}")
    digest = pilot_c.prompt_source_sha256(context, instructions)
    if digest != task["prompt_source_sha256"]:
        raise PilotCRunError(f"Prompt source hash mismatch for {task['slug']}")
    if task["target_signature"] not in instructions[0]:
        raise PilotCRunError(f"Turn-1 instruction lacks the frozen signature for {task['slug']}")
    return {
        "benchmark": {"name": "SR-Eval", "commit": config["benchmark_commit"], "hash_id": task["hash_id"]},
        "metadata": metadata,
        "turn_datas": turns,
    }


def condition_suffix(config: dict[str, Any], task: dict[str, Any], condition: str) -> str:
    if condition not in NEW_CONDITIONS:
        raise PilotCRunError(f"Pilot C may generate only: {', '.join(NEW_CONDITIONS)}")
    guardrails = read_text_spec(config["prompting"]["guardrails"])
    suffix = "\n\n" + guardrails.rstrip() + "\n"
    if condition == "engineering-guardrails-retrieval":
        header = read_text_spec(config["prompting"]["retrieval_header"])
        packet = ROOT / task["retrieval_packet"]
        if pilot_c.sha256(packet) != task["retrieval_sha256"]:
            raise PilotCRunError(f"Retrieval packet hash mismatch for {task['slug']}")
        suffix += "\n" + header.rstrip() + "\n\n" + packet.read_text(encoding="utf-8").rstrip() + "\n"
    return suffix


def render_prompt(
    config: dict[str, Any],
    task: dict[str, Any],
    packet: dict[str, Any],
    condition: str,
    turn_data: dict[str, Any],
    previous_code: str,
) -> str:
    turn = int(turn_data["turn_num"])
    prompt_key = "turn_1_template" if turn == 1 else "later_turn_template"
    template = read_text_spec(config["prompting"][prompt_key])
    prompt = pilot_a.render_prompt(
        template,
        context=packet["metadata"]["context"],
        code=previous_code,
        instruction=turn_data["instruction"],
    ).rstrip()
    prompt += condition_suffix(config, task, condition)
    if "{{" in prompt or "}}" in prompt:
        raise PilotCRunError(f"Unresolved template placeholder for {task['slug']} turn {turn}")
    if turn == 1 and task["target_signature"] not in prompt:
        raise PilotCRunError(f"Rendered turn-1 prompt lacks target signature for {task['slug']}")
    return prompt


def run_id(
    config: dict[str, Any], task: dict[str, Any], condition: str, repetition: int
) -> str:
    return f"{config['batch_id']}-{condition}-{task['slug']}-r{repetition:02d}"


def prompt_hashes(config: dict[str, Any], task: dict[str, Any], condition: str) -> dict[str, str]:
    prompting = config["prompting"]
    keys = ["system_prompt", "turn_1_template", "later_turn_template", "guardrails"]
    hashes = {prompting[key]["path"]: prompting[key]["sha256"] for key in keys}
    if condition == "engineering-guardrails-retrieval":
        hashes[prompting["retrieval_header"]["path"]] = prompting["retrieval_header"]["sha256"]
        hashes[task["retrieval_packet"]] = task["retrieval_sha256"]
    return hashes


def initial_record(
    config: dict[str, Any], task: dict[str, Any], condition: str, repetition: int
) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "batch_id": config["batch_id"],
        "run_id": run_id(config, task, condition, repetition),
        "repetition": repetition,
        "task_hash": task["hash_id"],
        "task_slug": task["slug"],
        "condition": condition,
        "benchmark_commit": config["benchmark_commit"],
        "product_interface": config["execution"]["product_interface"],
        "session_id": None,
        "model": {
            "display_name": config["model"]["display_name"],
            "slug": config["model"]["slug"],
            "reasoning_effort": config["model"]["reasoning_effort"],
            "automatic_routing": config["model"]["automatic_routing"],
            "snapshot": None,
        },
        "started_at": pilot_a.utc_now(),
        "completed_at": None,
        "prompt_sha256": prompt_hashes(config, task, condition),
        "prompt_source_sha256": task["prompt_source_sha256"],
        "retrieval_packet_sha256": (
            task["retrieval_sha256"] if condition == "engineering-guardrails-retrieval" else None
        ),
        "turns": [],
    }


def selected_tasks(config: dict[str, Any], slug: str | None, all_tasks: bool) -> list[dict[str, Any]]:
    if all_tasks:
        return config["tasks"]
    matches = [task for task in config["tasks"] if task["slug"] == slug]
    if not matches:
        raise PilotCRunError(f"Unknown Pilot C task: {slug}")
    return matches


def selected_repetitions(config: dict[str, Any], repetition: int | None) -> list[int]:
    maximum = config["runs_per_task_condition"]
    if repetition is None:
        return list(range(1, maximum + 1))
    if not 1 <= repetition <= maximum:
        raise PilotCRunError(f"Repetition must be between 1 and {maximum}")
    return [repetition]


def preflight(config: dict[str, Any], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "batch_id": config["batch_id"],
        "model_contacted": False,
        "tasks": [],
    }
    for task in config["tasks"]:
        packet = load_packet(config, task)
        task_report: dict[str, Any] = {"slug": task["slug"], "hash_id": task["hash_id"], "conditions": []}
        rendered: dict[str, list[str]] = {}
        for condition in NEW_CONDITIONS:
            prompts: list[str] = []
            condition_dir = output / condition / task["slug"]
            condition_dir.mkdir(parents=True, exist_ok=True)
            for turn_data in packet["turn_datas"]:
                turn = int(turn_data["turn_num"])
                prompt = render_prompt(
                    config,
                    task,
                    packet,
                    condition,
                    turn_data,
                    "" if turn == 1 else PREVIOUS_CODE_SENTINEL,
                )
                prompts.append(prompt)
                (condition_dir / f"turn-{turn}.prompt.txt").write_text(prompt, encoding="utf-8")
            rendered[condition] = prompts
            task_report["conditions"].append(
                {
                    "condition": condition,
                    "repetitions": config["runs_per_task_condition"],
                    "turns_per_repetition": len(prompts),
                    "planned_run_ids": [
                        run_id(config, task, condition, repetition)
                        for repetition in range(1, config["runs_per_task_condition"] + 1)
                    ],
                    "prompt_skeleton_sha256": [
                        hashlib.sha256(prompt.encode("utf-8")).hexdigest() for prompt in prompts
                    ],
                }
            )
        for turn, (guardrail, retrieval) in enumerate(
            zip(rendered["engineering-guardrails"], rendered["engineering-guardrails-retrieval"]), 1
        ):
            if not retrieval.startswith(guardrail):
                raise PilotCRunError(
                    f"Retrieval condition differs before appended material for {task['slug']} turn {turn}"
                )
        report["tasks"].append(task_report)
    report["summary"] = {
        "tasks": len(config["tasks"]),
        "repositories": len({task["repo"] for task in config["tasks"]}),
        "conditions": len(NEW_CONDITIONS),
        "repetitions": config["runs_per_task_condition"],
        "new_trajectories": len(config["tasks"]) * len(NEW_CONDITIONS) * config["runs_per_task_condition"],
        "prompt_skeletons": sum(
            condition["turns_per_repetition"] * condition["repetitions"]
            for task in report["tasks"]
            for condition in task["conditions"]
        ),
    }
    pilot_a.write_json(output / "summary.json", report)
    return report


def run_task(
    codex: Path,
    config: dict[str, Any],
    task: dict[str, Any],
    condition: str,
    repetition: int,
) -> None:
    packet = load_packet(config, task)
    protocol = runtime_protocol(config)
    record = initial_record(config, task, condition, repetition)
    run_dir = OUTPUT_ROOT / record["run_id"]
    session_dir = SESSION_ROOT / record["run_id"]
    if run_dir.exists():
        raise PilotCRunError(f"Run already exists; refusing to overwrite {run_dir}")
    if session_dir.exists():
        raise PilotCRunError(f"Session directory already exists; refusing to reuse {session_dir}")
    run_dir.mkdir(parents=True)
    session_dir.mkdir(parents=True)
    record_path = run_dir / "record.json"
    session_id: str | None = None
    previous_code = ""
    try:
        for turn_data in packet["turn_datas"]:
            turn = int(turn_data["turn_num"])
            prompt = render_prompt(config, task, packet, condition, turn_data, previous_code)
            prompt_path = run_dir / f"turn-{turn}.prompt.txt"
            events_path = run_dir / f"turn-{turn}.events.jsonl"
            stderr_path = run_dir / f"turn-{turn}.stderr.txt"
            raw_path = run_dir / f"turn-{turn}.raw.md"
            prompt_path.write_text(prompt, encoding="utf-8")
            print(
                f"[{condition}/{task['slug']}/r{repetition:02d}] generating turn {turn}/{task['turns']}",
                flush=True,
            )
            events, raw_response = pilot_a.run_turn(
                codex=codex,
                protocol=protocol,
                session_dir=session_dir,
                session_id=session_id,
                prompt=prompt,
                raw_path=raw_path,
                events_path=events_path,
                stderr_path=stderr_path,
            )
            if session_id is None:
                session_id = pilot_a.event_session_id(events)
                if session_id is None:
                    raise PilotCRunError("Initial CLI event stream contains no thread_id")
                record["session_id"] = session_id
            extracted_code = pilot_a.extract_java(raw_response)
            record["turns"].append(
                {
                    "turn": turn,
                    "instruction": turn_data["instruction"],
                    "prompt": prompt,
                    "raw_response": raw_response,
                    "extracted_code": extracted_code,
                    "tests": [],
                    "cumulatively_correct": None,
                    "usage": pilot_a.event_usage(events),
                }
            )
            previous_code = extracted_code
            pilot_a.write_json(record_path, record)
        record["completed_at"] = pilot_a.utc_now()
        pilot_a.write_json(record_path, record)
        print(f"[{condition}/{task['slug']}/r{repetition:02d}] complete: {record_path}", flush=True)
    except Exception as exc:
        pilot_a.write_json(
            run_dir / "failure.json",
            {
                "run_id": record["run_id"],
                "failed_at": pilot_a.utc_now(),
                "completed_turns": len(record["turns"]),
                "error": str(exc),
            },
        )
        if record["turns"]:
            pilot_a.write_json(record_path, record)
        raise


def resolve_codex(value: str) -> Path:
    path = Path(value).resolve()
    if path.is_file():
        return path
    resolved = shutil.which(value)
    if resolved:
        return Path(resolved)
    raise PilotCRunError(f"Codex CLI not found: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--task")
    selection.add_argument("--all", action="store_true")
    selection.add_argument("--preflight", action="store_true")
    parser.add_argument("--condition", choices=NEW_CONDITIONS)
    parser.add_argument("--repetition", type=int)
    parser.add_argument("--codex", default=str(DEFAULT_CODEX))
    parser.add_argument("--preflight-output", default=str(PREFLIGHT_ROOT))
    parser.add_argument("--preflight-summary", default=str(PREFLIGHT_SUMMARY))
    args = parser.parse_args(argv)
    try:
        config = pilot_c.read_json(CONFIG_PATH)
        errors = pilot_c.validate_config(config, check_dataset=True)
        if errors:
            raise PilotCRunError("Invalid Pilot C configuration:\n- " + "\n- ".join(errors))
        codex = resolve_codex(args.codex)
        pilot_a.verify_codex_version(codex, runtime_protocol(config))
        if args.preflight:
            if args.condition is not None or args.repetition is not None:
                raise PilotCRunError("--condition and --repetition are not used with --preflight")
            report = preflight(config, Path(args.preflight_output).resolve())
            summary_path = Path(args.preflight_summary).resolve()
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            pilot_a.write_json(summary_path, report)
            print(
                "Preflight passed: "
                f"{report['summary']['repositories']} repositories, "
                f"{report['summary']['new_trajectories']} trajectories, "
                f"{report['summary']['prompt_skeletons']} prompt skeletons; model not contacted\n"
                f"Summary: {summary_path}"
            )
            return 0
        if args.condition is None:
            raise PilotCRunError("--condition is required for generation")
        for task in selected_tasks(config, args.task, args.all):
            for repetition in selected_repetitions(config, args.repetition):
                run_task(codex, config, task, args.condition, repetition)
        return 0
    except (PilotCRunError, pilot_a.GenerationError, pilot_c.PilotCError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
