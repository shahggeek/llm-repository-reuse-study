#!/usr/bin/env python3
"""Validate, decode, and summarize the frozen industry-expert responses."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = ROOT / "results/pilot/industry-expert-review-intake-frozen.json"
KEY_PATH = ROOT / "results/pilot/industry-expert-review-blind-key.json"
CSV_PATH = ROOT / "results/pilot/industry-expert-review-responses.csv"
SUMMARY_PATH = ROOT / "results/pilot/industry-expert-review-summary.json"

RETRIEVAL = "engineering-guardrails-retrieval"
PRIMARY_ROLES = {"reuse contrast", "reuse-persistence contrast"}
EXPECTED_SHEETS = ["Instructions", "Reviewer Profile", "Case Guide", "Review", "Code"]

PROFILE_FIELDS = [
    "Reviewer code",
    "Consent to anonymized research use",
    "Professional software-development experience",
    "Professional Java experience",
    "Current or most recent role level",
    "Code-review frequency",
    "Experience with large multi-module codebases",
    "Coding-assistant use in normal work",
    "Used an LLM/AI assistant for this review",
    "AI assistance details",
    "Review date",
]

REVIEW_FIELDS = [
    "case_id",
    "preferred implementation",
    "decision A",
    "decision B",
    "repository fit A (1–5)",
    "repository fit B (1–5)",
    "maintainability A (1–5)",
    "maintainability B (1–5)",
    "duplicated repository behavior",
    "higher future-change risk",
    "confidence",
    "rationale",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        return value.strip()
    return value


def experience_category(value: Any) -> str:
    value = normalize(value)
    if isinstance(value, (int, float)):
        years = float(value)
        if years <= 5:
            return "1–5 years"
        if years <= 10:
            return "6–10 years"
        if years <= 15:
            return "11–15 years"
        return "16+ years"
    return str(value)


def load_numbers_tables(path: Path) -> dict[str, list[list[Any]]]:
    try:
        from numbers_parser import Document
    except ImportError as exc:  # pragma: no cover - exercised by the Make target
        raise SystemExit(
            "numbers-parser is required; run the industry-review target from the Makefile"
        ) from exc

    document = Document(str(path))
    sheets = [sheet.name for sheet in document.sheets]
    if sheets != EXPECTED_SHEETS:
        raise ValueError(f"{path.name}: unexpected sheets {sheets}")

    tables: dict[str, list[list[Any]]] = {}
    for sheet in document.sheets:
        if len(sheet.tables) != 1:
            raise ValueError(f"{path.name}: {sheet.name} must contain exactly one table")
        tables[sheet.name] = sheet.tables[0].rows(values_only=True)
    return tables


def profile_from_rows(rows: list[list[Any]]) -> dict[str, Any]:
    profile = {str(row[0]): normalize(row[1]) for row in rows[4:15]}
    missing = set(PROFILE_FIELDS) - set(profile)
    if missing:
        raise ValueError(f"missing profile fields: {sorted(missing)}")
    profile["Professional software-development experience"] = experience_category(
        profile["Professional software-development experience"]
    )
    profile["Professional Java experience"] = experience_category(
        profile["Professional Java experience"]
    )
    return profile


def mapped_choice(choice: str, retrieval_variant: str, comparator_variant: str) -> str:
    if choice == retrieval_variant:
        return "retrieval"
    if choice == comparator_variant:
        return "comparator"
    return choice.lower().replace(" ", "-")


def validate_profile(profile: dict[str, Any], expected_code: str) -> None:
    if profile["Reviewer code"] != expected_code:
        raise ValueError(f"expected reviewer {expected_code}, got {profile['Reviewer code']}")
    if profile["Consent to anonymized research use"] != "Yes":
        raise ValueError(f"{expected_code}: consent must be Yes")
    if profile["Used an LLM/AI assistant for this review"] != "No":
        raise ValueError(f"{expected_code}: primary analysis requires AI use No")


def parse_review_rows(
    rows: list[list[Any]],
    reviewer_code: str,
    case_key: dict[str, dict[str, Any]],
    source_path: str,
    source_sha256: str,
) -> list[dict[str, Any]]:
    headers = [normalize(value) for value in rows[3][:12]]
    if headers != REVIEW_FIELDS:
        raise ValueError(f"{reviewer_code}: review headers changed")

    output: list[dict[str, Any]] = []
    for source_row in rows[4:10]:
        values = [normalize(value) for value in source_row[:12]]
        record = dict(zip(REVIEW_FIELDS, values, strict=True))
        case_id = record["case_id"]
        if case_id not in case_key:
            raise ValueError(f"{reviewer_code}: unexpected case {case_id}")
        for field in REVIEW_FIELDS[1:]:
            if record[field] in (None, ""):
                raise ValueError(f"{reviewer_code}/{case_id}: missing {field}")
        for field in (
            "repository fit A (1–5)",
            "repository fit B (1–5)",
            "maintainability A (1–5)",
            "maintainability B (1–5)",
        ):
            score = int(record[field])
            if score not in range(1, 6):
                raise ValueError(f"{reviewer_code}/{case_id}: invalid {field}={score}")
            record[field] = score

        key = case_key[case_id]
        retrieval_variant = "A" if key["variant_a"]["condition"] == RETRIEVAL else "B"
        comparator_variant = "B" if retrieval_variant == "A" else "A"
        preferred = record["preferred implementation"]
        if preferred not in {"A", "B", "No material difference", "Unsure"}:
            raise ValueError(f"{reviewer_code}/{case_id}: invalid preference {preferred}")

        decoded = {
            "reviewer_code": reviewer_code,
            "case_id": case_id,
            "task_slug": key["task_slug"],
            "turn": key["turn"],
            "expected_role": key["expected_role"],
            "source_path": source_path,
            "source_sha256": source_sha256,
            "retrieval_variant": retrieval_variant,
            "comparator_variant": comparator_variant,
            "comparator_condition": key[f"variant_{comparator_variant.lower()}"]["condition"],
            "preferred_arm": mapped_choice(preferred, retrieval_variant, comparator_variant),
            "retrieval_decision": record[f"decision {retrieval_variant}"],
            "comparator_decision": record[f"decision {comparator_variant}"],
            "retrieval_repository_fit": record[f"repository fit {retrieval_variant} (1–5)"],
            "comparator_repository_fit": record[f"repository fit {comparator_variant} (1–5)"],
            "retrieval_maintainability": record[f"maintainability {retrieval_variant} (1–5)"],
            "comparator_maintainability": record[f"maintainability {comparator_variant} (1–5)"],
            "duplicated_behavior_arm": mapped_choice(
                record["duplicated repository behavior"], retrieval_variant, comparator_variant
            ),
            "higher_future_risk_arm": mapped_choice(
                record["higher future-change risk"], retrieval_variant, comparator_variant
            ),
            "confidence": record["confidence"],
            "rationale": record["rationale"],
        }
        decoded["repository_fit_delta"] = (
            decoded["retrieval_repository_fit"] - decoded["comparator_repository_fit"]
        )
        decoded["maintainability_delta"] = (
            decoded["retrieval_maintainability"] - decoded["comparator_maintainability"]
        )
        output.append(decoded)

    expected_cases = list(case_key)
    observed_cases = [record["case_id"] for record in output]
    if observed_cases != expected_cases:
        raise ValueError(f"{reviewer_code}: cases changed: {observed_cases}")
    return output


def counts(records: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(sorted(Counter(str(record[field]) for record in records).items()))


def delta_summary(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [int(record[field]) for record in records]
    return {
        "median": float(median(values)),
        "positive": sum(value > 0 for value in values),
        "zero": sum(value == 0 for value in values),
        "negative": sum(value < 0 for value in values),
        "observations": len(values),
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "observations": len(records),
        "preferred_arm": counts(records, "preferred_arm"),
        "retrieval_decision": counts(records, "retrieval_decision"),
        "comparator_decision": counts(records, "comparator_decision"),
        "repository_fit_delta": delta_summary(records, "repository_fit_delta"),
        "maintainability_delta": delta_summary(records, "maintainability_delta"),
        "duplicated_behavior_arm": counts(records, "duplicated_behavior_arm"),
        "higher_future_risk_arm": counts(records, "higher_future_risk_arm"),
        "confidence": counts(records, "confidence"),
    }


def build_summary(
    records: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    intake: dict[str, Any],
) -> dict[str, Any]:
    per_case = {}
    for case_id in sorted({record["case_id"] for record in records}):
        case_records = [record for record in records if record["case_id"] == case_id]
        item = summarize_records(case_records)
        item.update(
            {
                "task_slug": case_records[0]["task_slug"],
                "turn": case_records[0]["turn"],
                "expected_role": case_records[0]["expected_role"],
                "comparator_condition": case_records[0]["comparator_condition"],
            }
        )
        per_case[case_id] = item

    primary = [record for record in records if record["expected_role"] in PRIMARY_ROLES]
    controls = [record for record in records if record["expected_role"] not in PRIMARY_ROLES]
    per_reviewer = {}
    for reviewer_code in sorted({record["reviewer_code"] for record in records}):
        reviewer_records = [record for record in records if record["reviewer_code"] == reviewer_code]
        per_reviewer[reviewer_code] = summarize_records(reviewer_records)

    return {
        "schema_version": 1,
        "status": "decoded-after-frozen-intake",
        "recruitment_closed_on": intake["recruitment_closed_on"],
        "reviewers": len(profiles),
        "cases": len(per_case),
        "judgments": len(records),
        "inference_boundary": (
            "Descriptive purposive evidence only; IE-RV-104 and IE-RV-105 are dependent "
            "checkpoints from one nodeArrayMerge lineage."
        ),
        "profiles": profiles,
        "all_cases": summarize_records(records),
        "primary_contrasts": {
            "case_ids": sorted({record["case_id"] for record in primary}),
            **summarize_records(primary),
            "dependent_lineage_note": (
                "IE-RV-104 and IE-RV-105 are two checkpoints from the same trajectory, "
                "not independent replications."
            ),
        },
        "controls": {
            "case_ids": sorted({record["case_id"] for record in controls}),
            **summarize_records(controls),
        },
        "per_case": per_case,
        "per_reviewer": per_reviewer,
    }


def main() -> None:
    intake = load_json(INTAKE_PATH)
    if intake["status"] != "frozen-before-treatment-decoding":
        raise ValueError("intake must be frozen before decoding")
    key = load_json(KEY_PATH)
    case_key = {case["case_id"]: case for case in key["cases"]}

    profiles: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    for response in intake["responses"]:
        if not response["included"]:
            continue
        path = ROOT / response["path"]
        actual_sha256 = sha256(path)
        if actual_sha256 != response["sha256"]:
            raise ValueError(f"hash mismatch for {response['path']}")
        tables = load_numbers_tables(path)
        profile = profile_from_rows(tables["Reviewer Profile"])
        validate_profile(profile, response["reviewer_code"])
        profiles.append(
            {
                "reviewer_code": profile["Reviewer code"],
                "software_development_experience": profile[
                    "Professional software-development experience"
                ],
                "java_experience": profile["Professional Java experience"],
                "role_level": profile["Current or most recent role level"],
                "code_review_frequency": profile["Code-review frequency"],
                "large_multimodule_experience": profile[
                    "Experience with large multi-module codebases"
                ],
                "normal_coding_assistant_use": profile["Coding-assistant use in normal work"],
                "review_date": profile["Review date"],
            }
        )
        records.extend(
            parse_review_rows(
                tables["Review"],
                response["reviewer_code"],
                case_key,
                response["path"],
                response["sha256"],
            )
        )

    summary = build_summary(records, profiles, intake)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fieldnames = list(records[0])
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

    print(
        f"Frozen practitioner analysis complete: {summary['reviewers']} reviewers, "
        f"{summary['cases']} cases, {summary['judgments']} judgments"
    )


if __name__ == "__main__":
    main()
