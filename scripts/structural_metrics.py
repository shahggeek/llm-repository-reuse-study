#!/usr/bin/env python3
"""Extract parser-backed structural metrics for eligible Pilot A checkpoints."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "experiment/config/protocol.json"
MANIFEST_PATH = ROOT / "experiment/config/pilot-tasks.json"
AMENDMENT_PATH = ROOT / "experiment/config/pilot-a-amendment.json"
AUDIT_PATH = ROOT / "results/pilot/prompt-context-sufficiency-audit.json"
FUNCTIONAL_SUMMARY_PATH = ROOT / "results/pilot/pilot-a-adjusted-functional-summary.json"
PACKET_DIR = ROOT / "work/task-packets"
AMENDMENT_PACKET_DIR = ROOT / "work/amendment-task-packets"
ORIGINAL_RECORD_DIR = ROOT / "data/generated-trajectories/pilot-a"
AMENDMENT_RECORD_DIR = ROOT / "data/generated-trajectories/pilot-a-amendment"
CSV_OUTPUT = ROOT / "data/processed/pilot-a-structural-metrics.csv"
JSON_OUTPUT = ROOT / "data/processed/pilot-a-structural-metrics.json"
SUMMARY_OUTPUT = ROOT / "results/pilot/pilot-a-structural-summary.json"
EPSILON = 1e-9

METRIC_NAMES = (
    "physical_lines",
    "source_lines_nonblank_noncomment",
    "statement_count",
    "cyclomatic_complexity",
    "cognitive_complexity_approx",
    "max_control_nesting",
    "branch_count",
    "method_invocation_count",
    "constructor_invocation_count",
    "unique_call_target_count",
    "parameter_count",
    "return_count",
    "throw_count",
    "local_variable_count",
    "lambda_count",
    "code_smell_count",
)

DECISION_NODES = {
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "do_statement",
    "catch_clause",
    "ternary_expression",
}
NESTING_NODES = DECISION_NODES | {
    "switch_expression",
    "synchronized_statement",
    "lambda_expression",
}
STATEMENT_NODES = {
    "assert_statement",
    "break_statement",
    "continue_statement",
    "do_statement",
    "enhanced_for_statement",
    "expression_statement",
    "for_statement",
    "if_statement",
    "local_variable_declaration",
    "return_statement",
    "switch_expression",
    "synchronized_statement",
    "throw_statement",
    "try_statement",
    "while_statement",
    "yield_statement",
}


class MetricsError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MetricsError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MetricsError(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def descendants(node: Any) -> Iterable[Any]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def node_text(node: Any, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8")


def strip_java_comments(code: str) -> str:
    output: list[str] = []
    index = 0
    state = "code"
    while index < len(code):
        char = code[index]
        next_char = code[index + 1] if index + 1 < len(code) else ""
        if state == "code":
            if char == "/" and next_char == "/":
                state = "line-comment"
                output.extend("  ")
                index += 2
                continue
            if char == "/" and next_char == "*":
                state = "block-comment"
                output.extend("  ")
                index += 2
                continue
            output.append(char)
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            index += 1
            continue
        if state == "line-comment":
            if char == "\n":
                output.append(char)
                state = "code"
            else:
                output.append(" ")
            index += 1
            continue
        if state == "block-comment":
            if char == "*" and next_char == "/":
                output.extend("  ")
                index += 2
                state = "code"
            else:
                output.append("\n" if char == "\n" else " ")
                index += 1
            continue
        output.append(char)
        if char == "\\" and index + 1 < len(code):
            output.append(code[index + 1])
            index += 2
            continue
        if (state == "string" and char == '"') or (state == "char" and char == "'"):
            state = "code"
        index += 1
    return "".join(output)


def source_line_count(code: str) -> int:
    return sum(bool(line.strip()) for line in strip_java_comments(code).splitlines())


def parser() -> Any:
    try:
        from tree_sitter import Language, Parser
        import tree_sitter_java
        import lizard  # noqa: F401
    except ImportError as exc:
        raise MetricsError(
            "Structural parser dependencies are missing. Run through `make structural-pilot`."
        ) from exc
    return Parser(Language(tree_sitter_java.language()))


def parse_method(code: str) -> tuple[Any, bytes, dict[str, Any]]:
    prefix = "class __MetricsWrapper {\n"
    suffix = "\n}\n"
    wrapped = (prefix + code + suffix).encode("utf-8")
    tree = parser().parse(wrapped)
    error_nodes = [
        node
        for node in descendants(tree.root_node)
        if node.type == "ERROR" or node.is_missing
    ]
    methods = [node for node in descendants(tree.root_node) if node.type == "method_declaration"]
    if tree.root_node.has_error or error_nodes:
        locations = [f"{node.start_point.row + 1}:{node.start_point.column + 1}" for node in error_nodes]
        raise MetricsError(f"Java parse error at {', '.join(locations) or 'unknown location'}")
    if len(methods) != 1:
        raise MetricsError(f"Expected one method declaration, found {len(methods)}")
    return methods[0], wrapped, {
        "parser": "tree-sitter-java",
        "tree_sitter_version": "0.25.2",
        "tree_sitter_java_version": "0.23.5",
        "error_nodes": 0,
    }


def switch_case_count(method: Any, source: bytes) -> int:
    total = 0
    for node in descendants(method):
        if node.type not in {"switch_label", "switch_rule"}:
            continue
        text = node_text(node, source).lstrip()
        if text.startswith("case ") or text.startswith("case\n"):
            total += 1
    return total


def boolean_decision_count(method: Any) -> int:
    total = 0
    for node in descendants(method):
        if node.type != "binary_expression":
            continue
        total += sum(child.type in {"&&", "||"} for child in node.children)
    return total


def max_control_nesting(method: Any) -> int:
    maximum = 0

    def visit(node: Any, depth: int) -> None:
        nonlocal maximum
        next_depth = depth
        if node.type in NESTING_NODES:
            next_depth += 1
            maximum = max(maximum, next_depth)
        for child in node.named_children:
            visit(child, next_depth)

    body = method.child_by_field_name("body")
    if body is not None:
        visit(body, 0)
    return maximum


def cognitive_complexity(method: Any) -> int:
    score = 0

    def visit(node: Any, nesting: int) -> None:
        nonlocal score
        next_nesting = nesting
        if node.type in DECISION_NODES | {"switch_expression"}:
            score += 1 + nesting
            next_nesting += 1
        elif node.type == "else":
            score += 1
        elif node.type == "binary_expression":
            score += sum(child.type in {"&&", "||"} for child in node.children)
        elif node.type == "lambda_expression":
            next_nesting += 1
        for child in node.named_children:
            visit(child, next_nesting)

    body = method.child_by_field_name("body")
    if body is not None:
        visit(body, 0)
    return score


def parameter_count(method: Any) -> int:
    parameters = method.child_by_field_name("parameters")
    if parameters is None:
        return 0
    return sum(
        child.type in {"formal_parameter", "spread_parameter", "receiver_parameter"}
        for child in parameters.named_children
    )


def call_targets(method: Any, source: bytes) -> tuple[list[str], list[str]]:
    methods: list[str] = []
    constructors: list[str] = []
    for node in descendants(method):
        if node.type == "method_invocation":
            name = node.child_by_field_name("name")
            methods.append(node_text(name, source) if name is not None else "<unknown>")
        elif node.type == "object_creation_expression":
            type_node = node.child_by_field_name("type")
            constructors.append(
                f"new {node_text(type_node, source)}" if type_node is not None else "new <unknown>"
            )
    return methods, constructors


def code_smells(metrics: dict[str, Any]) -> list[str]:
    smells: list[str] = []
    if metrics["source_lines_nonblank_noncomment"] > 40:
        smells.append("long-method>40-sloc")
    if metrics["cyclomatic_complexity"] > 10:
        smells.append("high-cyclomatic>10")
    if metrics["max_control_nesting"] > 3:
        smells.append("deep-control-nesting>3")
    if metrics["parameter_count"] > 4:
        smells.append("long-parameter-list>4")
    return smells


def lizard_cyclomatic_complexity(code: str) -> int:
    try:
        import lizard
    except ImportError as exc:
        raise MetricsError(
            "Lizard validation dependency is missing. Run through `make structural-pilot`."
        ) from exc
    result = lizard.analyze_file.analyze_source_code(
        "__MetricsWrapper.java", f"class __MetricsWrapper {{\n{code}\n}}"
    )
    if len(result.function_list) != 1:
        raise MetricsError(
            f"Lizard expected one method declaration, found {len(result.function_list)}"
        )
    return int(result.function_list[0].cyclomatic_complexity)


def extract_metrics(code: str) -> dict[str, Any]:
    method, source, diagnostics = parse_method(code)
    nodes = list(descendants(method))
    method_calls, constructors = call_targets(method, source)
    switch_cases = switch_case_count(method, source)
    boolean_decisions = boolean_decision_count(method)
    decision_count = sum(node.type in DECISION_NODES for node in nodes)
    branch_count = decision_count + switch_cases
    cyclomatic = 1 + decision_count + switch_cases + boolean_decisions
    lizard_cyclomatic = lizard_cyclomatic_complexity(code)
    if cyclomatic != lizard_cyclomatic:
        raise MetricsError(
            f"Cyclomatic validation mismatch: tree-sitter={cyclomatic}, "
            f"lizard={lizard_cyclomatic}"
        )
    diagnostics["lizard_version"] = "1.17.31"
    diagnostics["lizard_cyclomatic_complexity"] = lizard_cyclomatic
    metrics: dict[str, Any] = {
        "physical_lines": len(code.splitlines()),
        "source_lines_nonblank_noncomment": source_line_count(code),
        "statement_count": sum(node.type in STATEMENT_NODES for node in nodes),
        "cyclomatic_complexity": cyclomatic,
        "cognitive_complexity_approx": cognitive_complexity(method),
        "max_control_nesting": max_control_nesting(method),
        "branch_count": branch_count,
        "method_invocation_count": len(method_calls),
        "constructor_invocation_count": len(constructors),
        "unique_call_target_count": len(set(method_calls + constructors)),
        "parameter_count": parameter_count(method),
        "return_count": sum(node.type == "return_statement" for node in nodes),
        "throw_count": sum(node.type == "throw_statement" for node in nodes),
        "local_variable_count": sum(
            node.type == "variable_declarator"
            and node.parent is not None
            and node.parent.type == "local_variable_declaration"
            for node in nodes
        ),
        "lambda_count": sum(node.type == "lambda_expression" for node in nodes),
        "method_call_targets": sorted(set(method_calls)),
        "constructor_call_targets": sorted(set(constructors)),
        "parser_diagnostics": diagnostics,
    }
    smells = code_smells(metrics)
    metrics["code_smells"] = smells
    metrics["code_smell_count"] = len(smells)
    return metrics


def adjusted_metadata(
    manifest: dict[str, Any], amendment: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    replaced = {row["replaces"]["slug"] for row in amendment["replacements"]}
    metadata = {
        task["slug"]: task for task in manifest["tasks"] if task["slug"] not in replaced
    }
    amendment_slugs: set[str] = set()
    for replacement in amendment["replacements"]:
        task = replacement["task"]
        metadata[task["slug"]] = task
        amendment_slugs.add(task["slug"])
    return metadata, amendment_slugs


def audit_index(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {task["slug"]: task for task in audit["tasks"]}


def packet_for(slug: str, amendment_slugs: set[str]) -> dict[str, Any]:
    directory = AMENDMENT_PACKET_DIR if slug in amendment_slugs else PACKET_DIR
    return read_json(directory / f"{slug}.json")


def record_for(
    slug: str,
    metadata: dict[str, Any],
    amendment_slugs: set[str],
    protocol: dict[str, Any],
    amendment: dict[str, Any],
) -> dict[str, Any]:
    batch_id = amendment["batch_id"] if slug in amendment_slugs else protocol["pilot_a"]["batch_id"]
    directory = AMENDMENT_RECORD_DIR if slug in amendment_slugs else ORIGINAL_RECORD_DIR
    path = directory / f"{batch_id}-{slug}-01" / "record.json"
    record = read_json(path)
    if record.get("task_hash") != metadata["hash_id"]:
        raise MetricsError(f"{slug}: run-record hash mismatch")
    return record


def overhead(generated: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for metric in METRIC_NAMES:
        generated_value = generated[metric]
        reference_value = reference[metric]
        difference = generated_value - reference_value
        result[metric] = {
            "absolute": difference,
            "normalized": difference / (reference_value + EPSILON),
            "reference_zero": reference_value == 0,
        }
    return result


def selected_pairs() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    protocol = read_json(PROTOCOL_PATH)
    manifest = read_json(MANIFEST_PATH)
    amendment = read_json(AMENDMENT_PATH)
    audit = read_json(AUDIT_PATH)
    functional = read_json(FUNCTIONAL_SUMMARY_PATH)
    metadata, amendment_slugs = adjusted_metadata(manifest, amendment)
    audit_rows = audit_index(audit)
    excluded = {(row["slug"], row["turn"]) for row in functional["exclusions"]}
    strict_excluded_tasks = {
        task["slug"]
        for task in audit["tasks"]
        if task["classification"]
        in {"inferable-consistent", "underspecified-integration-types"}
    }
    rows: list[dict[str, Any]] = []
    for slug, task in metadata.items():
        packet = packet_for(slug, amendment_slugs)
        record = record_for(slug, task, amendment_slugs, protocol, amendment)
        if packet.get("study_task", {}).get("hash_id") != task["hash_id"]:
            raise MetricsError(f"{slug}: packet hash mismatch")
        turns_by_number = {int(turn["turn"]): turn for turn in record["turns"]}
        for turn_data in packet["turn_datas"]:
            turn = int(turn_data["turn_num"])
            generated_turn = turns_by_number[turn]
            if generated_turn.get("cumulatively_correct") is not True:
                continue
            if (slug, turn) in excluded:
                continue
            rows.append(
                {
                    "task_slug": slug,
                    "task_hash": task["hash_id"],
                    "repository": task["repo"],
                    "turn": turn,
                    "batch_id": record["batch_id"],
                    "run_id": record["run_id"],
                    "prompt_context_classification": audit_rows[slug]["classification"],
                    "strict_explicit_signature_subgroup": slug not in strict_excluded_tasks,
                    "generated_code": generated_turn["extracted_code"],
                    "reference_code": turn_data["solution"],
                }
            )
    if len(rows) != 24:
        raise MetricsError(f"Expected 24 eligible correct pairs, found {len(rows)}")
    if sum(row["strict_explicit_signature_subgroup"] for row in rows) != 16:
        raise MetricsError("Expected 16 strict explicit-signature pairs")
    return rows, {
        "protocol": protocol,
        "amendment": amendment,
        "audit": audit,
        "functional": functional,
    }


def build_metric_record(pair: dict[str, Any]) -> dict[str, Any]:
    generated_code = pair["generated_code"]
    reference_code = pair["reference_code"]
    generated = extract_metrics(generated_code)
    reference = extract_metrics(reference_code)
    return {
        **{key: value for key, value in pair.items() if not key.endswith("_code")},
        "generated_code_sha256": sha256_text(generated_code),
        "reference_code_sha256": sha256_text(reference_code),
        "generated": generated,
        "reference": reference,
        "overhead": overhead(generated, reference),
    }


def describe(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "mean": statistics.fmean(values),
        "median": statistics.median(values),
        "minimum": min(values),
        "maximum": max(values),
        "positive": sum(value > 0 for value in values),
        "zero": sum(value == 0 for value in values),
        "negative": sum(value < 0 for value in values),
    }


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise MetricsError("Cannot compute a percentile of an empty list")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def clustered_bootstrap(
    rows: list[dict[str, Any]], metric: str, iterations: int = 5000
) -> dict[str, Any]:
    groups: dict[str, list[float]] = {}
    for row in rows:
        groups.setdefault(row["task_slug"], []).append(
            row["overhead"][metric]["absolute"]
        )
    task_slugs = sorted(groups)
    if not task_slugs:
        return {"iterations": iterations, "clusters": 0}
    seed_material = f"pilot-a-structural-v1:{metric}:{','.join(task_slugs)}"
    seed = int.from_bytes(hashlib.sha256(seed_material.encode()).digest()[:8], "big")
    rng = random.Random(seed)
    means: list[float] = []
    medians: list[float] = []
    for _ in range(iterations):
        values: list[float] = []
        for _ in task_slugs:
            sampled_slug = rng.choice(task_slugs)
            values.extend(groups[sampled_slug])
        means.append(statistics.fmean(values))
        medians.append(statistics.median(values))
    return {
        "iterations": iterations,
        "clusters": len(task_slugs),
        "seed_sha256": hashlib.sha256(seed_material.encode()).hexdigest(),
        "mean_95_percentile_interval": [percentile(means, 0.025), percentile(means, 0.975)],
        "median_95_percentile_interval": [
            percentile(medians, 0.025),
            percentile(medians, 0.975),
        ],
    }


def summarize_rows(
    rows: list[dict[str, Any]], *, include_uncertainty: bool = False
) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for metric in METRIC_NAMES:
        summary[metric] = {
            "generated": describe([row["generated"][metric] for row in rows]),
            "reference": describe([row["reference"][metric] for row in rows]),
            "absolute_overhead": describe(
                [row["overhead"][metric]["absolute"] for row in rows]
            ),
            "normalized_overhead": describe(
                [
                    row["overhead"][metric]["normalized"]
                    for row in rows
                    if not row["overhead"][metric]["reference_zero"]
                    and math.isfinite(row["overhead"][metric]["normalized"])
                ]
            ),
            "reference_zero_count": sum(
                row["overhead"][metric]["reference_zero"] for row in rows
            ),
        }
        if include_uncertainty:
            summary[metric]["clustered_bootstrap_absolute_overhead"] = clustered_bootstrap(
                rows, metric
            )
    return summary


def grouped_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = sorted({row[field] for row in rows}, key=str)
    return {
        str(value): {
            "checkpoints": sum(row[field] == value for row in rows),
            "metrics": summarize_rows([row for row in rows if row[field] == value]),
        }
        for value in values
    }


def csv_rows(records: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    identity = [
        "task_slug",
        "task_hash",
        "repository",
        "turn",
        "batch_id",
        "run_id",
        "prompt_context_classification",
        "strict_explicit_signature_subgroup",
        "generated_code_sha256",
        "reference_code_sha256",
    ]
    fields = list(identity)
    for metric in METRIC_NAMES:
        fields.extend(
            [
                f"generated_{metric}",
                f"reference_{metric}",
                f"absolute_overhead_{metric}",
                f"normalized_overhead_{metric}",
                f"reference_zero_{metric}",
            ]
        )
    rows: list[dict[str, Any]] = []
    for record in records:
        row = {field: record[field] for field in identity}
        for metric in METRIC_NAMES:
            row[f"generated_{metric}"] = record["generated"][metric]
            row[f"reference_{metric}"] = record["reference"][metric]
            row[f"absolute_overhead_{metric}"] = record["overhead"][metric]["absolute"]
            row[f"normalized_overhead_{metric}"] = record["overhead"][metric]["normalized"]
            row[f"reference_zero_{metric}"] = record["overhead"][metric]["reference_zero"]
        rows.append(row)
    return fields, rows


def write_csv(records: list[dict[str, Any]]) -> None:
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields, rows = csv_rows(records)
    temporary = CSV_OUTPUT.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(CSV_OUTPUT)


def main() -> int:
    try:
        pairs, inputs = selected_pairs()
        records = [build_metric_record(pair) for pair in pairs]
        records.sort(key=lambda row: (row["task_slug"], row["turn"]))
        write_csv(records)
        write_json(
            JSON_OUTPUT,
            {
                "schema_version": 1,
                "metric_definitions": {
                    "epsilon": EPSILON,
                    "metric_names": list(METRIC_NAMES),
                    "cognitive_complexity": "Documented deterministic approximation; not SonarQube output.",
                    "smell_thresholds": {
                        "long_method_sloc": 40,
                        "high_cyclomatic": 10,
                        "deep_control_nesting": 3,
                        "long_parameter_list": 4,
                    },
                },
                "source_batches": [
                    inputs["protocol"]["pilot_a"]["batch_id"],
                    inputs["amendment"]["batch_id"],
                ],
                "records": records,
            },
        )
        strict_records = [row for row in records if row["strict_explicit_signature_subgroup"]]
        summary = {
            "schema_version": 1,
            "checkpoint_pairs": len(records),
            "trajectory_count": len({row["task_slug"] for row in records}),
            "strict_explicit_signature_checkpoint_pairs": len(strict_records),
            "strict_explicit_signature_trajectory_count": len(
                {row["task_slug"] for row in strict_records}
            ),
            "all_eligible_correct": summarize_rows(records, include_uncertainty=True),
            "strict_explicit_signature": summarize_rows(
                strict_records, include_uncertainty=True
            ),
            "by_turn": grouped_summary(records, "turn"),
            "by_repository": grouped_summary(records, "repository"),
            "processed_artifacts": {
                "csv": str(CSV_OUTPUT.relative_to(ROOT)),
                "json": str(JSON_OUTPUT.relative_to(ROOT)),
                "csv_sha256": hashlib.sha256(CSV_OUTPUT.read_bytes()).hexdigest(),
                "json_sha256": hashlib.sha256(JSON_OUTPUT.read_bytes()).hexdigest(),
            },
            "interpretation_status": "descriptive-pilot-only",
        }
        write_json(SUMMARY_OUTPUT, summary)
        print(
            f"Structural metrics: {len(records)} checkpoint pairs across "
            f"{summary['trajectory_count']} trajectories"
        )
        print(
            f"Strict subgroup: {len(strict_records)} checkpoint pairs across "
            f"{summary['strict_explicit_signature_trajectory_count']} trajectories"
        )
        print(f"CSV: {CSV_OUTPUT}")
        print(f"Summary: {SUMMARY_OUTPUT}")
        return 0
    except (MetricsError, KeyError, TypeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
