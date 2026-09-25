#!/usr/bin/env python3
"""Render, preflight, and run the frozen Pilot B trajectories."""

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
import pilot_b  # noqa: E402


CONFIG_PATH = ROOT / "experiment/config/pilot-b.json"
PILOT_A_PACKET_DIR = ROOT / "work/task-packets"
AMENDMENT_PACKET_DIR = ROOT / "work/amendment-task-packets"
OUTPUT_ROOT = ROOT / "data/generated-trajectories/pilot-b"
SESSION_ROOT = ROOT / "work/pilot-b-sessions"
PREFLIGHT_ROOT = ROOT / "work/pilot-b-preflight"
PREFLIGHT_SUMMARY = ROOT / "results/pilot/pilot-b-preflight-summary.json"
DEFAULT_CODEX = ROOT / ".tools/codex-cli-0.153.0/node_modules/.bin/codex"
NEW_CONDITIONS = ("engineering-guardrails", "engineering-guardrails-retrieval")
PREVIOUS_CODE_SENTINEL = "/* PREVIOUS GENERATED METHOD: supplied only during the actual resumed run */"


class PilotBRunError(RuntimeError):
    pass


def read_text_spec(spec: dict[str, Any]) -> str:
    path = ROOT / spec["path"]
    if pilot_b.sha256(path) != spec["sha256"]:
        raise PilotBRunError(f"Frozen file hash mismatch: {spec['path']}")
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


def packet_path(task: dict[str, Any]) -> Path:
    if task["packet_source"] == "pilot-a-amendment":
        return AMENDMENT_PACKET_DIR / f"{task['slug']}.json"
    if task["packet_source"] == "pilot-a":
        return PILOT_A_PACKET_DIR / f"{task['slug']}.json"
    raise PilotBRunError(f"Unknown packet source for {task['slug']}")


def load_packet(task: dict[str, Any]) -> dict[str, Any]:
    packet = pilot_a.read_json(packet_path(task))
    if packet.get("study_task", {}).get("hash_id") != task["hash_id"]:
        raise PilotBRunError(f"Task packet hash mismatch for {task['slug']}")
    turns = packet.get("turn_datas")
    metadata = packet.get("metadata")
    if not isinstance(turns, list) or len(turns) != task["turns"] or not isinstance(metadata, dict):
        raise PilotBRunError(f"Malformed task packet for {task['slug']}")
    instructions = [turn.get("instruction") for turn in turns if isinstance(turn, dict)]
    if len(instructions) != task["turns"] or any(not isinstance(item, str) for item in instructions):
        raise PilotBRunError(f"Malformed task instructions for {task['slug']}")
    context = metadata.get("context")
    if not isinstance(context, str):
        raise PilotBRunError(f"Missing prompt context for {task['slug']}")
    digest = pilot_b.prompt_source_sha256(context, instructions)
    if digest != task["prompt_source_sha256"]:
        raise PilotBRunError(f"Prompt source hash mismatch for {task['slug']}")
    if task["target_signature"] not in instructions[0]:
        raise PilotBRunError(f"Turn-1 instruction lacks the frozen target signature for {task['slug']}")
    return packet


def baseline_record_path(task: dict[str, Any]) -> Path:
    directory = "pilot-a-amendment" if task["packet_source"] == "pilot-a-amendment" else "pilot-a"
    return ROOT / "data/generated-trajectories" / directory / task["baseline_run_id"] / "record.json"


def validate_baseline_record(task: dict[str, Any]) -> tuple[Path, str]:
    path = baseline_record_path(task)
    record = pilot_a.read_json(path)
    if record.get("run_id") != task["baseline_run_id"]:
        raise PilotBRunError(f"Baseline run ID mismatch for {task['slug']}")
    if record.get("task_hash") != task["hash_id"] or record.get("condition") != "baseline":
        raise PilotBRunError(f"Baseline identity mismatch for {task['slug']}")
    if record.get("completed_at") is None or len(record.get("turns", [])) != task["turns"]:
        raise PilotBRunError(f"Baseline run is incomplete for {task['slug']}")
    return path, pilot_b.sha256(path)


def condition_suffix(config: dict[str, Any], task: dict[str, Any], condition: str) -> str:
    if condition not in NEW_CONDITIONS:
        raise PilotBRunError(f"Pilot B may generate only: {', '.join(NEW_CONDITIONS)}")
    guardrails = read_text_spec(config["prompting"]["guardrails"])
    suffix = "\n\n" + guardrails.rstrip() + "\n"
    if condition == "engineering-guardrails-retrieval":
        header = read_text_spec(config["prompting"]["retrieval_header"])
        packet = ROOT / task["retrieval_packet"]
        if pilot_b.sha256(packet) != task["retrieval_sha256"]:
            raise PilotBRunError(f"Retrieval packet hash mismatch for {task['slug']}")
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
        raise PilotBRunError(f"Unresolved template placeholder for {task['slug']} turn {turn}")
    if turn == 1 and task["target_signature"] not in prompt:
        raise PilotBRunError(f"Rendered turn-1 prompt lacks target signature for {task['slug']}")
    return prompt


def run_id(config: dict[str, Any], task: dict[str, Any], condition: str) -> str:
    return f"{config['batch_id']}-{condition}-{task['slug']}-01"


def prompt_hashes(config: dict[str, Any], task: dict[str, Any], condition: str) -> dict[str, str]:
    prompting = config["prompting"]
    keys = ["system_prompt", "turn_1_template", "later_turn_template", "guardrails"]
    hashes = {prompting[key]["path"]: prompting[key]["sha256"] for key in keys}
    if condition == "engineering-guardrails-retrieval":
        hashes[prompting["retrieval_header"]["path"]] = prompting["retrieval_header"]["sha256"]
        hashes[task["retrieval_packet"]] = task["retrieval_sha256"]
    return hashes


def initial_record(config: dict[str, Any], task: dict[str, Any], condition: str) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "batch_id": config["batch_id"],
        "run_id": run_id(config, task, condition),
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
    tasks = config["tasks"]
    if all_tasks:
        return tasks
    matches = [task for task in tasks if task["slug"] == slug]
    if not matches:
        raise PilotBRunError(f"Unknown Pilot B task: {slug}")
    return matches


def preflight(config: dict[str, Any], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "schema_version": 1,
        "batch_id": config["batch_id"],
        "model_contacted": False,
        "tasks": [],
    }
    for task in config["tasks"]:
        packet = load_packet(task)
        baseline_path, baseline_digest = validate_baseline_record(task)
        task_report: dict[str, Any] = {
            "slug": task["slug"],
            "hash_id": task["hash_id"],
            "baseline_record": str(baseline_path.relative_to(ROOT)),
            "baseline_record_sha256": baseline_digest,
            "conditions": [],
        }
        rendered_by_condition: dict[str, list[str]] = {}
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
                path = condition_dir / f"turn-{turn}.prompt.txt"
                path.write_text(prompt, encoding="utf-8")
            rendered_by_condition[condition] = prompts
            task_report["conditions"].append(
                {
                    "condition": condition,
                    "turns": len(prompts),
                    "prompt_skeleton_sha256": [
                        hashlib.sha256(prompt.encode("utf-8")).hexdigest() for prompt in prompts
                    ],
                }
            )
        guardrail_prompts = rendered_by_condition["engineering-guardrails"]
        retrieval_prompts = rendered_by_condition["engineering-guardrails-retrieval"]
        for turn, (guardrail, retrieval) in enumerate(zip(guardrail_prompts, retrieval_prompts), 1):
            if not retrieval.startswith(guardrail):
                raise PilotBRunError(
                    f"Retrieval condition differs before its appended packet for {task['slug']} turn {turn}"
                )
        report["tasks"].append(task_report)
    report["summary"] = {
        "tasks": len(report["tasks"]),
        "conditions": len(NEW_CONDITIONS),
        "new_trajectories": len(report["tasks"]) * len(NEW_CONDITIONS),
        "prompt_skeletons": sum(
            condition["turns"]
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
) -> None:
    packet = load_packet(task)
    validate_baseline_record(task)
    protocol = runtime_protocol(config)
    record = initial_record(config, task, condition)
    run_dir = OUTPUT_ROOT / record["run_id"]
    if run_dir.exists():
        raise PilotBRunError(f"Run already exists; refusing to overwrite {run_dir}")
    session_dir = SESSION_ROOT / record["run_id"]
    if session_dir.exists():
        raise PilotBRunError(f"Session directory already exists; refusing to reuse {session_dir}")
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
                f"[{condition}/{task['slug']}] generating turn {turn}/{task['turns']}",
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
                    raise PilotBRunError("Initial CLI event stream contains no thread_id")
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
        print(f"[{condition}/{task['slug']}] complete: {record_path}", flush=True)
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
    raise PilotBRunError(f"Codex CLI not found: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--task")
    selection.add_argument("--all", action="store_true")
    selection.add_argument(
        "--preflight",
        action="store_true",
        help="render and verify all 12 planned trajectories without model contact",
    )
    parser.add_argument("--condition", choices=NEW_CONDITIONS)
    parser.add_argument("--codex", default=str(DEFAULT_CODEX))
    parser.add_argument("--preflight-output", default=str(PREFLIGHT_ROOT))
    parser.add_argument("--preflight-summary", default=str(PREFLIGHT_SUMMARY))
    args = parser.parse_args(argv)
    try:
        config = pilot_b.read_json(CONFIG_PATH)
        errors = pilot_b.validate_config(config, check_dataset=True)
        if errors:
            raise PilotBRunError("Invalid Pilot B configuration:\n- " + "\n- ".join(errors))
        codex = resolve_codex(args.codex)
        pilot_a.verify_codex_version(codex, runtime_protocol(config))
        if args.preflight:
            if args.condition is not None:
                raise PilotBRunError("--condition is not used with --preflight")
            report = preflight(config, Path(args.preflight_output).resolve())
            summary_path = Path(args.preflight_summary).resolve()
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            pilot_a.write_json(summary_path, report)
            print(
                "Preflight passed: "
                f"{report['summary']['tasks']} tasks, "
                f"{report['summary']['new_trajectories']} new trajectories, "
                f"{report['summary']['prompt_skeletons']} prompt skeletons; model not contacted\n"
                f"Summary: {summary_path}"
            )
            return 0
        if args.condition is None:
            raise PilotBRunError("--condition is required for generation")
        for task in selected_tasks(config, args.task, args.all):
            run_task(codex, config, task, args.condition)
        return 0
    except (PilotBRunError, pilot_a.GenerationError, pilot_b.PilotBError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
