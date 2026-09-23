#!/usr/bin/env python3
"""Run the frozen Pilot A trajectories through isolated Codex CLI sessions."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "experiment/config/protocol.json"
MANIFEST_PATH = ROOT / "experiment/config/pilot-tasks.json"
AMENDMENT_PATH = ROOT / "experiment/config/pilot-a-amendment.json"
PACKET_DIR = ROOT / "work/task-packets"
AMENDMENT_PACKET_DIR = ROOT / "work/amendment-task-packets"
OUTPUT_ROOT = ROOT / "data/generated-trajectories/pilot-a"
AMENDMENT_OUTPUT_ROOT = ROOT / "data/generated-trajectories/pilot-a-amendment"
SESSION_ROOT = ROOT / "work/pilot-a-sessions"
AMENDMENT_SESSION_ROOT = ROOT / "work/pilot-a-amendment-sessions"
DEFAULT_CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
JAVA_BLOCK = re.compile(r"```java\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
VERSION_NUMBER = re.compile(r"(\d+\.\d+\.\d+)")


class GenerationError(RuntimeError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GenerationError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GenerationError(f"Expected a JSON object in {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prompt_hashes(protocol: dict[str, Any]) -> dict[str, str]:
    return {
        relative: sha256(ROOT / relative)
        for key in ("system_prompt", "turn_1_template", "later_turn_template", "guardrails")
        for relative in (protocol["prompting"][key],)
    }


def required_codex_version(protocol: dict[str, Any]) -> str:
    product_interface = protocol.get("execution", {}).get("product_interface", "")
    match = VERSION_NUMBER.search(product_interface)
    if match is None:
        raise GenerationError("Frozen protocol has no parseable Codex CLI version")
    return match.group(1)


def installed_codex_version(codex: Path) -> str:
    completed = subprocess.run(
        [str(codex), "--version"],
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout + "\n" + completed.stderr).strip()
    match = VERSION_NUMBER.search(output)
    if completed.returncode != 0 or match is None:
        raise GenerationError(f"Cannot determine Codex CLI version from: {output}")
    return match.group(1)


def verify_codex_version(codex: Path, protocol: dict[str, Any]) -> str:
    expected = required_codex_version(protocol)
    actual = installed_codex_version(codex)
    if actual != expected:
        raise GenerationError(
            f"Codex CLI version mismatch: frozen protocol requires {expected}, found {actual}"
        )
    return actual


def render_prompt(template: str, *, context: str = "", code: str = "", instruction: str) -> str:
    return (
        template.replace("{{CONTEXT}}", context)
        .replace("{{PREVIOUS_CODE}}", code)
        .replace("{{INSTRUCTION}}", instruction)
    )


def extract_java(raw_response: str) -> str:
    blocks = JAVA_BLOCK.findall(raw_response)
    if len(blocks) != 1:
        raise GenerationError(
            f"Expected exactly one Java Markdown block, found {len(blocks)}"
        )
    code = blocks[0].strip()
    if not code:
        raise GenerationError("The Java Markdown block is empty")
    return code


def parse_events(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise GenerationError(f"Invalid CLI event at line {line_number}: {exc}") from exc
        if not isinstance(value, dict):
            raise GenerationError(f"CLI event at line {line_number} is not an object")
        events.append(value)
    return events


def find_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = find_key(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_key(child, key)
            if found is not None:
                return found
    return None


def event_session_id(events: list[dict[str, Any]]) -> str | None:
    for event in events:
        value = find_key(event, "thread_id")
        if isinstance(value, str) and value:
            return value
    return None


def event_usage(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        value = find_key(event, "usage")
        if isinstance(value, dict):
            return value
    return None


def config_args(protocol: dict[str, Any]) -> list[str]:
    system_path = (ROOT / protocol["prompting"]["system_prompt"]).resolve()
    effort = protocol["model"]["reasoning_effort"].lower()
    return [
        "--ignore-user-config",
        "--strict-config",
        "-c",
        f'model_reasoning_effort="{effort}"',
        "-c",
        f'model_instructions_file="{system_path}"',
        "-c",
        'web_search="disabled"',
    ]


def run_turn(
    *,
    codex: Path,
    protocol: dict[str, Any],
    session_dir: Path,
    session_id: str | None,
    prompt: str,
    raw_path: Path,
    events_path: Path,
    stderr_path: Path,
) -> tuple[list[dict[str, Any]], str]:
    model = protocol["model"]["slug"]
    common = config_args(protocol)
    if session_id is None:
        command = [
            str(codex),
            "exec",
            "--model",
            model,
            "--sandbox",
            "read-only",
            "--cd",
            str(session_dir),
            "--skip-git-repo-check",
            *common,
            "--json",
            "--output-last-message",
            str(raw_path),
            "-",
        ]
    else:
        command = [
            str(codex),
            "exec",
            "resume",
            "--model",
            model,
            *common,
            "--json",
            "--output-last-message",
            str(raw_path),
            session_id,
            "-",
        ]
    completed = subprocess.run(
        command,
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )
    events_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise GenerationError(
            f"Codex CLI exited {completed.returncode}: {completed.stderr.strip()}"
        )
    events = parse_events(completed.stdout)
    try:
        raw_response = raw_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise GenerationError(f"CLI did not produce {raw_path}: {exc}") from exc
    return events, raw_response


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def amendment_tasks(amendment: dict[str, Any]) -> list[dict[str, Any]]:
    replacements = amendment.get("replacements")
    if not isinstance(replacements, list):
        raise GenerationError("Amendment replacements must be an array")
    tasks = [replacement.get("task") for replacement in replacements]
    if any(not isinstance(task, dict) for task in tasks):
        raise GenerationError("Every amendment replacement must contain a task object")
    return tasks


def run_spec(protocol: dict[str, Any], amendment: dict[str, Any] | None) -> dict[str, Any]:
    if amendment is None:
        return {
            "batch_id": protocol["pilot_a"]["batch_id"],
            "condition": protocol["pilot_a"]["condition"],
            "tasks": None,
            "packet_dir": PACKET_DIR,
            "output_root": OUTPUT_ROOT,
            "session_root": SESSION_ROOT,
        }
    if amendment.get("status") != "amendment-frozen":
        raise GenerationError("Pilot A amendment is not frozen")
    if amendment.get("benchmark_commit") != protocol["benchmark"]["commit"]:
        raise GenerationError("Amendment and protocol benchmark revisions differ")
    if amendment.get("parent_batch_id") != protocol["pilot_a"]["batch_id"]:
        raise GenerationError("Amendment parent batch does not match Pilot A")
    if amendment.get("condition") != protocol["pilot_a"]["condition"]:
        raise GenerationError("Amendment condition differs from Pilot A")
    if amendment.get("runs_per_task") != 1:
        raise GenerationError("Amendment must use exactly one run per task")
    if amendment.get("protocol_sha256") != sha256(PROTOCOL_PATH):
        raise GenerationError("Amendment protocol hash does not match protocol.json")
    return {
        "batch_id": amendment["batch_id"],
        "condition": amendment["condition"],
        "tasks": amendment_tasks(amendment),
        "packet_dir": AMENDMENT_PACKET_DIR,
        "output_root": AMENDMENT_OUTPUT_ROOT,
        "session_root": AMENDMENT_SESSION_ROOT,
    }


def initial_record(
    protocol: dict[str, Any], task: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any]:
    batch_id = spec["batch_id"]
    run_id = f"{batch_id}-{task['slug']}-01"
    return {
        "schema_version": 1,
        "batch_id": batch_id,
        "run_id": run_id,
        "task_hash": task["hash_id"],
        "task_slug": task["slug"],
        "condition": spec["condition"],
        "benchmark_commit": protocol["benchmark"]["commit"],
        "product_interface": protocol["execution"]["product_interface"],
        "session_id": None,
        "model": {
            "display_name": protocol["model"]["display_name"],
            "slug": protocol["model"]["slug"],
            "reasoning_effort": protocol["model"]["reasoning_effort"],
            "automatic_routing": protocol["model"]["automatic_routing"],
            "snapshot": None,
        },
        "started_at": utc_now(),
        "completed_at": None,
        "prompt_sha256": prompt_hashes(protocol),
        "turns": [],
    }


def run_task(
    codex: Path, protocol: dict[str, Any], task: dict[str, Any], spec: dict[str, Any]
) -> None:
    packet = read_json(spec["packet_dir"] / f"{task['slug']}.json")
    if packet.get("study_task", {}).get("hash_id") != task["hash_id"]:
        raise GenerationError(f"Task packet mismatch for {task['slug']}")

    record = initial_record(protocol, task, spec)
    run_dir = spec["output_root"] / record["run_id"]
    record_path = run_dir / "record.json"
    if record_path.exists():
        raise GenerationError(f"Run already exists; refusing to overwrite {record_path}")
    run_dir.mkdir(parents=True, exist_ok=False)
    session_dir = spec["session_root"] / record["run_id"]
    session_dir.mkdir(parents=True, exist_ok=False)

    turn_one_template = (ROOT / protocol["prompting"]["turn_1_template"]).read_text(encoding="utf-8")
    later_template = (ROOT / protocol["prompting"]["later_turn_template"]).read_text(encoding="utf-8")
    session_id: str | None = None
    previous_code = ""

    try:
        for turn_data in packet["turn_datas"]:
            turn = int(turn_data["turn_num"])
            prompt = render_prompt(
                turn_one_template if turn == 1 else later_template,
                context=packet["metadata"]["context"],
                code=previous_code,
                instruction=turn_data["instruction"],
            )
            prompt_path = run_dir / f"turn-{turn}.prompt.txt"
            events_path = run_dir / f"turn-{turn}.events.jsonl"
            stderr_path = run_dir / f"turn-{turn}.stderr.txt"
            raw_path = run_dir / f"turn-{turn}.raw.md"
            prompt_path.write_text(prompt, encoding="utf-8")
            print(f"[{task['slug']}] generating turn {turn}/{task['turns']}", flush=True)
            events, raw_response = run_turn(
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
                session_id = event_session_id(events)
                if session_id is None:
                    raise GenerationError("Initial CLI event stream contains no thread_id")
                record["session_id"] = session_id
            extracted_code = extract_java(raw_response)
            record["turns"].append(
                {
                    "turn": turn,
                    "instruction": turn_data["instruction"],
                    "prompt": prompt,
                    "raw_response": raw_response,
                    "extracted_code": extracted_code,
                    "tests": [],
                    "cumulatively_correct": None,
                    "usage": event_usage(events),
                }
            )
            previous_code = extracted_code
            write_json(record_path, record)
        record["completed_at"] = utc_now()
        write_json(record_path, record)
        print(f"[{task['slug']}] complete: {record_path}", flush=True)
    except Exception as exc:
        write_json(
            run_dir / "failure.json",
            {
                "run_id": record["run_id"],
                "failed_at": utc_now(),
                "completed_turns": len(record["turns"]),
                "error": str(exc),
            },
        )
        if record["turns"]:
            write_json(record_path, record)
        raise


def selected_tasks(manifest: dict[str, Any], slug: str | None, all_tasks: bool) -> list[dict[str, Any]]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise GenerationError("Manifest tasks must be an array")
    if all_tasks:
        return tasks
    matches = [task for task in tasks if task.get("slug") == slug]
    if not matches:
        raise GenerationError(f"Unknown Pilot A task: {slug}")
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--task")
    choice.add_argument("--all", action="store_true")
    choice.add_argument(
        "--preflight",
        action="store_true",
        help="validate frozen inputs and CLI version without contacting the model",
    )
    parser.add_argument("--codex", default=str(DEFAULT_CODEX))
    parser.add_argument(
        "--amendment",
        action="store_true",
        help="run the frozen two-task Pilot A amendment in isolated directories",
    )
    args = parser.parse_args(argv)

    try:
        protocol = read_json(PROTOCOL_PATH)
        amendment = read_json(AMENDMENT_PATH) if args.amendment else None
        manifest = read_json(MANIFEST_PATH)
        spec = run_spec(protocol, amendment)
        if protocol.get("protocol_status") != "pilot-a-frozen":
            raise GenerationError("Protocol is not frozen for Pilot A")
        if manifest.get("benchmark_commit") != protocol["benchmark"]["commit"]:
            raise GenerationError("Manifest and protocol benchmark revisions differ")
        codex = Path(args.codex).resolve()
        if not codex.is_file():
            resolved = shutil.which(args.codex)
            if not resolved:
                raise GenerationError(f"Codex CLI not found: {args.codex}")
            codex = Path(resolved)
        verify_codex_version(codex, protocol)
        if args.preflight:
            task_count = len(spec["tasks"]) if args.amendment else len(manifest["tasks"])
            print(
                f"Preflight passed: {spec['batch_id']} ({task_count} tasks), "
                f"Codex CLI {required_codex_version(protocol)}"
            )
            return 0
        selection = {"tasks": spec["tasks"]} if args.amendment else manifest
        for task in selected_tasks(selection, args.task, args.all):
            run_task(codex, protocol, task, spec)
        return 0
    except (GenerationError, KeyError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
