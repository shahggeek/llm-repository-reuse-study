#!/usr/bin/env python3
"""Build and verify the sanitized SANER reproducibility artifact."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "artifacts"
PACKAGE_ID = "saner-2027-reproducibility-artifact-2026-10-03"

INCLUDE_FILES = (
    "Makefile",
    "README.md",
    "artifacts/SUBMISSION_ARTIFACT_README.md",
    "paper/README.md",
    "paper/claim-evidence-matrix.md",
    "paper/main.tex",
    "paper/references.bib",
    "paper/related-work-sources.md",
)

INCLUDE_ROOTS = (
    "analysis",
    "data/generated-trajectories",
    "data/processed",
    "data/reference-metrics",
    "docs",
    "environment",
    "experiment",
    "outputs",
    "paper/sections",
    "results/full-study",
    "results/pilot",
    "scripts",
    "tests",
    "work/amendment-task-packets",
    "work/pilot-b-preflight",
    "work/pilot-c-preflight",
    "work/task-packets",
)

EXCLUDED_PATHS = {
    "docs/resume-handoff.md",
    "docs/saner-industrial-ethics-inquiry-email.md",
    "paper/mock-review-2026-10-03.md",
    "paper/saner-readiness-audit.md",
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


@dataclass(frozen=True)
class ArtifactEntry:
    path: str
    content: bytes


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


def entry_for_path(path: Path) -> ArtifactEntry:
    relative = path.relative_to(ROOT).as_posix()
    if relative == "results/pilot/industry-expert-review-responses.csv":
        content = sanitized_practitioner_responses(path)
    elif relative == "results/pilot/industry-expert-review-intake-frozen.json":
        content = sanitized_practitioner_intake(path)
    else:
        content = path.read_bytes()
    return ArtifactEntry(relative, content)


def collect_entries() -> list[ArtifactEntry]:
    return [entry_for_path(path) for path in collect_paths()]


def reject_private_or_secret_content(entries: list[ArtifactEntry]) -> None:
    findings: list[str] = []
    for entry in entries:
        if any(pattern in entry.content for pattern in FORBIDDEN_CONTENT):
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
        "rendered_prompts": count("data/generated-trajectories/", ".prompt.txt"),
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
        "rendered_prompts": 147,
        "raw_model_outputs": 147,
        "model_event_streams": 147,
        "model_stderr_logs": 147,
        "functional_test_reports": 6,
        "review_workbooks": 4,
        "practitioner_response_rows": 24,
    }
    if counts != expected:
        raise RuntimeError(f"Artifact count mismatch: expected {expected}, found {counts}")


def build_manifest(entries: list[ArtifactEntry], source_commit: str) -> dict[str, Any]:
    protocol = json.loads((ROOT / "experiment/config/protocol.json").read_text())
    counts = experiment_counts(entries)
    validate_counts(counts)
    files = [
        {
            "path": entry.path,
            "bytes": len(entry.content),
            "sha256": sha256_bytes(entry.content),
        }
        for entry in entries
    ]
    return {
        "schema_version": 1,
        "package_id": PACKAGE_ID,
        "status": "sanitized-submission-candidate",
        "built_on": "2026-10-03",
        "source_repository": "https://github.com/shahggeek/llm-evolution-quality-study",
        "source_commit": source_commit,
        "benchmark": protocol["benchmark"],
        "model": protocol["model"],
        "execution": protocol["execution"],
        "experiment_counts": counts,
        "privacy": {
            "raw_practitioner_workbooks_included": False,
            "identity_mapping_included": False,
            "private_correspondence_included": False,
            "machine_specific_paths_permitted": False,
            "transformed_public_files": sorted(PRIVATE_SOURCE_PATHS),
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
                "Pilot A, amendment, Pilot B, and Pilot C protocols and exact prompts",
                "Raw model outputs, event streams, stderr, and run records",
                "Functional reports, processed metrics, reuse reviews, and adjudications",
                "Anonymous practitioner ratings, rationales, and descriptive summaries",
                "Analysis code, tests, decisions, manuscript sources, and claim controls",
            ],
            "excluded": [
                "Raw returned practitioner workbooks and identity/contact mappings",
                "Private correspondence, chair inquiry, internal handoff, and mock-review notes",
                "Pre-contact failure logs containing machine-specific paths",
                "SR-Eval clone, tool installations, caches, containers, and local sessions",
            ],
            "known_limitations": [
                "The model provider did not expose an immutable model snapshot identifier.",
                "Functional retesting requires the separately obtained pinned SR-Eval commit and container environment.",
                "A final archive license must be selected before public deposit.",
            ],
        },
        "release_blockers": [
            "Select and document the archive license and third-party-material treatment.",
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

This sanitized submission candidate covers Pilots A, B, and C plus the
anonymous practitioner validation. It contains {counts['run_records']} run
records, {counts['raw_model_outputs']} raw model turn outputs, and
{counts['practitioner_response_rows']} anonymous practitioner case responses.

Start with `artifacts/SUBMISSION_ARTIFACT_README.md`. Verify every file against
`MANIFEST.json` and the archive against the adjacent `.sha256` file. Raw
returned practitioner workbooks, identity mappings, correspondence, local
failure logs, and the benchmark clone are not included.

This package is a verified candidate, not the final public deposit. Select and
document an appropriate archive license before uploading it to Zenodo or
another permanent repository.
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


def main() -> int:
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
