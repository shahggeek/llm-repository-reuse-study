#!/usr/bin/env python3
"""Build and verify the privacy-filtered SANER public evidence artifact."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"
PACKAGE_ID = "saner-2027-public-evidence-candidate-2026-10-05"

INCLUDE_FILES = (
    ".github/workflows/verify.yml",
    "CITATION.cff",
    "LICENSE",
    "LICENSE_SCOPE.md",
    "Makefile",
    "NOTICE",
    "THIRD_PARTY_LICENSES.md",
    "pyproject.toml",
    "artifacts/PUBLIC_REPOSITORY_README.md",
    "artifacts/SUBMISSION_ARTIFACT_README.md",
    "docs/decisions.md",
    "docs/methodology.md",
    "docs/pilot-protocol.md",
    "docs/practitioner-ethics-record.md",
    "docs/prompt-context-audit.md",
)

INCLUDE_ROOTS = (
    "analysis",
    "data/generated-trajectories",
    "data/processed",
    "data/reference-metrics",
    "environment",
    "experiment",
    "results/pilot",
    "scripts",
    "tests",
)

EXCLUDED_PATHS = {
    "scripts/build_industry_expert_review_workbook.mjs",
    "scripts/build_pilot_b_reuse_review_workbook.mjs",
    "scripts/build_reuse_review_workbook.mjs",
    "scripts/extract_pilot_b_reuse_review.mjs",
    "scripts/freeze_pilot_evidence.py",
    "tests/test_industry_expert_review_package.py",
    "tests/test_paper_claims.py",
}

EXCLUDED_NAMES = {
    ".DS_Store",
    "__pycache__",
}

EXCLUDED_SUFFIXES = (
    ".aux",
    ".bbl",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".pdf",
    ".pyc",
    ".synctex.gz",
)

PRIVATE_SOURCE_PATHS = {
    "results/pilot/industry-expert-review-intake-frozen.json",
    "results/pilot/industry-expert-review-responses.csv",
}

FORBIDDEN_CONTENT = (
    b"/" + b"Users/",
    b"/" + b"home/",
    b"C:" + b"\\Users\\",
    b"Reviewers" + b"Work/",
    b"github" + b"_pat_",
    b"gh" + b"p_",
    b"sk" + b"-proj-",
    b"OPENAI" + b"_API_KEY=",
    b"GITHUB" + b"_TOKEN=",
)

EMAIL_PATTERN = re.compile(
    rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
UUID_PATTERN = re.compile(
    rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".sh",
    ".txt",
}
IDENTIFIER_KEYS = {"session_id", "thread_id"}
BENCHMARK_TEXT_OMISSION = (
    "[OMITTED FROM PUBLIC ARTIFACT: benchmark-authored prompt text is not "
    "redistributed because SR-Eval and MRG-Bench do not state a redistribution "
    "license. Use scripts/reconstruct_prompts.py with the separately obtained "
    "pinned SR-Eval checkout.]"
)


@dataclass(frozen=True)
class ArtifactEntry:
    path: str
    content: bytes
    source_sha256: str
    transformations: tuple[str, ...] = ()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_output(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT
    ).strip()


def require_clean_tree() -> str:
    status = git_output("status", "--porcelain")
    if status:
        raise RuntimeError(
            "Submission artifacts must be built from a clean committed tree. "
            f"Uncommitted paths:\n{status}"
        )
    return git_output("rev-parse", "HEAD")


def should_include(path: Path) -> bool:
    if not path.is_file():
        return False
    relative = path.relative_to(ROOT).as_posix()
    if relative in EXCLUDED_PATHS:
        return False
    if any(part in EXCLUDED_NAMES for part in path.relative_to(ROOT).parts):
        return False
    return not relative.endswith(EXCLUDED_SUFFIXES)


def collect_paths() -> list[Path]:
    selected: set[Path] = set()
    for relative in INCLUDE_FILES:
        path = ROOT / relative
        if should_include(path):
            selected.add(path)
    for relative in INCLUDE_ROOTS:
        root = ROOT / relative
        if root.exists():
            selected.update(path for path in root.rglob("*") if should_include(path))
    return sorted(selected, key=lambda path: path.relative_to(ROOT).as_posix())


def sanitized_practitioner_responses(path: Path) -> bytes:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("Practitioner response table is empty")
    removed = {"source_path", "source_sha256"}
    fieldnames = [name for name in rows[0] if name not in removed]
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({name: row[name] for name in fieldnames})
    return stream.getvalue().encode("utf-8")


def sanitized_practitioner_intake(path: Path) -> bytes:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["responses"] = [
        {
            "reviewer_code": response["reviewer_code"],
            "included": response["included"],
        }
        for response in data["responses"]
    ]
    data["public_release_note"] = (
        "Private returned-workbook paths and hashes are intentionally omitted "
        "from the public artifact. Original files remain unchanged in the "
        "author's private research record."
    )
    data["notes"] = [
        note
        for note in data.get("notes", [])
        if "Numbers exports" not in note and "original returned files" not in note.lower()
    ]
    return (json.dumps(data, indent=2) + "\n").encode("utf-8")


def omitted_prompt_file(content: bytes) -> bytes:
    digest = sha256_bytes(content)
    return (
        "# Benchmark-derived prompt omitted from the public artifact\n\n"
        f"Original SHA-256: `{digest}`\n\n"
        f"{BENCHMARK_TEXT_OMISSION}\n"
    ).encode("utf-8")


def sanitized_generated_record(content: bytes) -> bytes:
    data = json.loads(content.decode("utf-8"))
    for turn in data.get("turns", []):
        instruction = turn.get("instruction")
        prompt = turn.get("prompt")
        if isinstance(instruction, str):
            turn["instruction_source_sha256"] = sha256_bytes(instruction.encode("utf-8"))
            turn["instruction"] = BENCHMARK_TEXT_OMISSION
        if isinstance(prompt, str):
            turn["rendered_prompt_sha256"] = sha256_bytes(prompt.encode("utf-8"))
            turn["prompt"] = BENCHMARK_TEXT_OMISSION
    data["public_prompt_policy"] = {
        "benchmark_authored_text_included": False,
        "reconstruction_command": (
            "python3 scripts/reconstruct_prompts.py "
            "--sr-eval .cache/SR-Eval --output reconstructed-prompts"
        ),
    }
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def public_identifier(value: str) -> str:
    if value.startswith("session-"):
        return value
    return "session-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def sanitize_json_identifiers(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                public_identifier(item)
                if key in IDENTIFIER_KEYS and isinstance(item, str)
                else sanitize_json_identifiers(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_json_identifiers(item) for item in value]
    return value


def sanitize_json_content(content: bytes, json_lines: bool) -> bytes:
    text = content.decode("utf-8")
    if json_lines:
        values = [
            sanitize_json_identifiers(json.loads(line))
            for line in text.splitlines()
            if line.strip()
        ]
        return b"".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            + b"\n"
            for value in values
        )
    value = sanitize_json_identifiers(json.loads(text))
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def redact_emails(content: bytes) -> bytes:
    def replacement(match: re.Match[bytes]) -> bytes:
        digest = hashlib.sha256(match.group(0).lower()).hexdigest()[:10]
        return f"[email-redacted-{digest}]".encode("ascii")

    return EMAIL_PATTERN.sub(replacement, content)


def pseudonymize_embedded_identifiers(content: bytes) -> bytes:
    return UUID_PATTERN.sub(
        lambda match: public_identifier(match.group(0).decode("ascii")).encode("ascii"),
        content,
    )


def entry_for_path(path: Path) -> ArtifactEntry:
    relative = path.relative_to(ROOT).as_posix()
    public_relative = (
        "README.md"
        if relative == "artifacts/PUBLIC_REPOSITORY_README.md"
        else relative
    )
    source_content = path.read_bytes()
    transformations: list[str] = []
    if relative == "results/pilot/industry-expert-review-responses.csv":
        content = sanitized_practitioner_responses(path)
        transformations.append("removed-private-workbook-source-columns")
    elif relative == "results/pilot/industry-expert-review-intake-frozen.json":
        content = sanitized_practitioner_intake(path)
        transformations.append("removed-private-workbook-paths-and-hashes")
    elif relative.startswith("data/generated-trajectories/") and relative.endswith(
        ".prompt.txt"
    ):
        content = omitted_prompt_file(source_content)
        transformations.append("omitted-unlicensed-benchmark-prompt-text")
    elif relative.startswith("data/generated-trajectories/") and relative.endswith(
        "/record.json"
    ):
        content = sanitized_generated_record(source_content)
        transformations.append("omitted-unlicensed-benchmark-prompt-text")
    else:
        content = source_content
    if relative.startswith("data/generated-trajectories/") and path.suffix in {
        ".json",
        ".jsonl",
    }:
        sanitized = sanitize_json_content(content, path.suffix == ".jsonl")
        if sanitized != content:
            content = sanitized
            transformations.append("pseudonymized-provider-session-identifiers")
    if path.suffix in TEXT_SUFFIXES:
        redacted = redact_emails(content)
        if redacted != content:
            content = redacted
            transformations.append("redacted-email-addresses")
    if relative.startswith("data/generated-trajectories/"):
        pseudonymized = pseudonymize_embedded_identifiers(content)
        if pseudonymized != content:
            content = pseudonymized
            if "pseudonymized-provider-session-identifiers" not in transformations:
                transformations.append("pseudonymized-provider-session-identifiers")
    return ArtifactEntry(
        public_relative,
        content,
        sha256_bytes(source_content),
        tuple(transformations),
    )


def collect_entries() -> list[ArtifactEntry]:
    return [entry_for_path(path) for path in collect_paths()]


def reject_private_or_secret_content(entries: list[ArtifactEntry]) -> None:
    findings: list[str] = []
    for entry in entries:
        if (
            any(pattern in entry.content for pattern in FORBIDDEN_CONTENT)
            or EMAIL_PATTERN.search(entry.content)
            or (
                entry.path.startswith("data/generated-trajectories/")
                and UUID_PATTERN.search(entry.content)
            )
        ):
            findings.append(entry.path)
    if findings:
        raise RuntimeError(
            "Private, machine-specific, or possible credential material found: "
            + ", ".join(findings)
        )


def experiment_counts(entries: list[ArtifactEntry]) -> dict[str, int]:
    paths = [entry.path for entry in entries]

    def count(prefix: str, suffix: str) -> int:
        return sum(path.startswith(prefix) and path.endswith(suffix) for path in paths)

    return {
        "run_records": count("data/generated-trajectories/", "/record.json"),
        "prompt_omission_records": count(
            "data/generated-trajectories/", ".prompt.txt"
        ),
        "raw_model_outputs": count("data/generated-trajectories/", ".raw.md"),
        "model_event_streams": count("data/generated-trajectories/", ".events.jsonl"),
        "model_stderr_logs": count("data/generated-trajectories/", ".stderr.txt"),
        "functional_test_reports": count("results/pilot/generated-tests/", ".json"),
        "review_workbooks": count("outputs/", ".xlsx"),
        "practitioner_response_rows": max(
            0,
            next(
                entry.content.count(b"\n") - 1
                for entry in entries
                if entry.path == "results/pilot/industry-expert-review-responses.csv"
            ),
        ),
    }


def validate_counts(counts: dict[str, int]) -> None:
    expected = {
        "run_records": 44,
        "prompt_omission_records": 147,
        "raw_model_outputs": 147,
        "model_event_streams": 147,
        "model_stderr_logs": 147,
        "functional_test_reports": 6,
        "review_workbooks": 0,
        "practitioner_response_rows": 24,
    }
    if counts != expected:
        raise RuntimeError(f"Artifact count mismatch: expected {expected}, found {counts}")


def build_manifest(entries: list[ArtifactEntry], source_commit: str) -> dict[str, Any]:
    protocol = json.loads((ROOT / "experiment/config/protocol.json").read_text())
    counts = experiment_counts(entries)
    validate_counts(counts)
    files = []
    for entry in entries:
        item = {
            "path": entry.path,
            "bytes": len(entry.content),
            "sha256": sha256_bytes(entry.content),
        }
        if entry.transformations:
            item["source_sha256"] = entry.source_sha256
            item["transformations"] = list(entry.transformations)
        files.append(item)
    return {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "status": "privacy-filtered-public-evidence-candidate",
        "built_on": "2026-10-05",
        "source_repository": "private-working-repository",
        "source_commit": source_commit,
        "benchmark": protocol["benchmark"],
        "model": protocol["model"],
        "execution": protocol["execution"],
        "experiment_counts": counts,
        "privacy": {
            "raw_practitioner_workbooks_included": False,
            "identity_mapping_included": False,
            "private_correspondence_included": False,
            "manuscript_included": False,
            "raw_review_workbooks_included": False,
            "provider_session_identifiers_pseudonymized": True,
            "email_addresses_redacted": True,
            "benchmark_authored_prompt_text_included": False,
            "machine_specific_paths_permitted": False,
            "transformed_public_files": sorted(
                entry.path for entry in entries if entry.transformations
            ),
        },
        "verification": {
            "hash_algorithm": "SHA-256",
            "archive_format": "deterministic tar.gz",
            "tar_entry_mtime": 0,
            "tar_uid_gid": 0,
            "gzip_mtime": 0,
        },
        "scope": {
            "included": [
                "Pilot A, amendment, Pilot B, and Pilot C protocols and hash-bound prompt omission records",
                "Raw model outputs, event streams, stderr, and run records",
                "Functional reports, processed metrics, reuse reviews, and adjudications",
                "Anonymous practitioner ratings, rationales, and descriptive summaries",
                "Analysis code, tests, protocol decisions, and public reproduction guidance",
            ],
            "excluded": [
                "Manuscript sources, author metadata, and internal submission notes",
                "Raw returned practitioner workbooks and identity/contact mappings",
                "Reviewer-facing and completed spreadsheet workbooks",
                "Private correspondence, chair inquiry, internal handoff, and mock-review notes",
                "Pre-contact failure logs containing machine-specific paths",
                "SR-Eval clone, tool installations, caches, containers, and local sessions",
                "SR-Eval/MRG-Bench-authored task instructions and rendered prompt text; these are reconstructed from a separately obtained pinned checkout",
            ],
            "known_limitations": [
                "The model provider did not expose an immutable model snapshot identifier.",
                "Benchmark-authored task instructions and rendered prompt text are omitted because SR-Eval and MRG-Bench do not state a redistribution license; original hashes bind the omitted text and a reconstruction tool verifies it against a separately obtained checkout.",
                "Provider session identifiers are replaced by deterministic public pseudonyms.",
                "Some source evidence is Git-ignored in the private working repository; this manifest binds the exact packaged bytes.",
                "Functional retesting requires the separately obtained pinned SR-Eval commit and container environment.",
                "The repository license applies only to study-authored material as defined in LICENSE_SCOPE.md.",
            ],
        },
        "release_blockers": [
            "Upload the verified archive to a stable repository and add its DOI to the manuscript.",
        ],
        "file_count": len(files),
        "total_uncompressed_bytes": sum(item["bytes"] for item in files),
        "files": files,
    }


def package_readme(manifest: dict[str, Any]) -> bytes:
    counts = manifest["experiment_counts"]
    text = f"""# SANER 2027 reproducibility artifact

Package: `{manifest['package_id']}`  
Source commit: `{manifest['source_commit']}`  
SR-Eval commit: `{manifest['benchmark']['commit']}`

This privacy- and license-filtered public evidence candidate covers Pilots A, B, and C plus the
anonymous practitioner validation. It contains {counts['run_records']} run
records, {counts['raw_model_outputs']} raw model turn outputs, and
{counts['practitioner_response_rows']} anonymous practitioner case responses.

Start with `artifacts/SUBMISSION_ARTIFACT_README.md`. Verify every file against
`MANIFEST.json` and the archive against the adjacent `.sha256` file. Raw
returned practitioner workbooks, identity mappings, correspondence, manuscript
sources, local failure logs, and the benchmark clone are not included. Provider
session identifiers are pseudonymized. Benchmark-authored task instructions and
rendered prompts are omitted because SR-Eval and MRG-Bench do not state a
redistribution license. Their original hashes are retained, and
`scripts/reconstruct_prompts.py` verifies exact reconstruction after the user
separately obtains the pinned SR-Eval checkout.

Study-authored material is licensed as described in `LICENSE_SCOPE.md`.
Third-party and evidence material is governed by `THIRD_PARTY_LICENSES.md`.
This package is a verified candidate, not the final permanent deposit.
"""
    return text.encode("utf-8")


def tar_info(name: str, size: int, mode: int = 0o644) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name=f"{PACKAGE_ID}/{name}")
    info.size = size
    info.mode = mode
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def write_archive(
    entries: list[ArtifactEntry], manifest: dict[str, Any], archive_path: Path
) -> None:
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    readme_bytes = package_readme(manifest)
    with archive_path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                archive.addfile(
                    tar_info("EVIDENCE_PACKAGE_README.md", len(readme_bytes)),
                    io.BytesIO(readme_bytes),
                )
                archive.addfile(
                    tar_info("MANIFEST.json", len(manifest_bytes)),
                    io.BytesIO(manifest_bytes),
                )
                for entry in entries:
                    archive.addfile(
                        tar_info(entry.path, len(entry.content)), io.BytesIO(entry.content)
                    )


def verify_archive(archive_path: Path, manifest: dict[str, Any]) -> None:
    expected = {item["path"]: item for item in manifest["files"]}
    root = f"{PACKAGE_ID}/"
    with tarfile.open(archive_path, "r:gz") as archive:
        members = {
            member.name[len(root) :]: member
            for member in archive.getmembers()
            if member.isfile() and member.name.startswith(root)
        }
        packaged = set(members) - {"EVIDENCE_PACKAGE_README.md", "MANIFEST.json"}
        if packaged != set(expected):
            raise RuntimeError("Archive membership differs from the manifest")
        for path, item in expected.items():
            extracted = archive.extractfile(members[path])
            if extracted is None:
                raise RuntimeError(f"Could not read archived file: {path}")
            content = extracted.read()
            if len(content) != item["bytes"] or sha256_bytes(content) != item["sha256"]:
                raise RuntimeError(f"Archive verification failed for {path}")
            if any(pattern in content for pattern in FORBIDDEN_CONTENT):
                raise RuntimeError(f"Forbidden content found after packaging: {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or verify the privacy-filtered public evidence package."
    )
    parser.add_argument(
        "--verify-inputs",
        action="store_true",
        help="validate the complete public input inventory without writing an archive",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.verify_inputs:
        entries = collect_entries()
        reject_private_or_secret_content(entries)
        counts = experiment_counts(entries)
        validate_counts(counts)
        print(json.dumps({"status": "valid", "experiment_counts": counts}, indent=2))
        return 0

    source_commit = require_clean_tree()
    entries = collect_entries()
    reject_private_or_secret_content(entries)
    manifest = build_manifest(entries, source_commit)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    archive_path = ARTIFACT_DIR / f"{PACKAGE_ID}.tar.gz"
    manifest_path = ARTIFACT_DIR / f"{PACKAGE_ID}.manifest.json"
    checksum_path = ARTIFACT_DIR / f"{PACKAGE_ID}.sha256"

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    write_archive(entries, manifest, archive_path)
    verify_archive(archive_path, manifest)
    archive_sha256 = sha256_file(archive_path)
    checksum_path.write_text(f"{archive_sha256}  {archive_path.name}\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "archive": str(archive_path.relative_to(ROOT)),
                "archive_bytes": archive_path.stat().st_size,
                "archive_sha256": archive_sha256,
                "manifest": str(manifest_path.relative_to(ROOT)),
                "files": manifest["file_count"],
                "experiment_counts": manifest["experiment_counts"],
                "source_commit": source_commit,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
