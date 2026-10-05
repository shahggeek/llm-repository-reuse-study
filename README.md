# Repository-Reuse Study — Public Evidence

This repository contains the privacy-filtered evidence for a study of
repository-level reuse in LLM-generated Java code under progressive software
evolution. It covers the Pilot A baseline and isolated amendment, the targeted
Pilot B guardrail/API-context mechanism probe, the Pilot C cross-repository
boundary check, independent semantic reuse review, and anonymous practitioner
validation.

This is an evidence repository, not the manuscript repository. It intentionally
excludes manuscript sources, author working notes, correspondence, raw returned
review workbooks, identity mappings, machine-specific failure logs, and local
tool or benchmark installations.

## Public history provenance

The public Git history is derived from the private working history by filtering
paths before publication. Original commit dates, messages, and public-safe
changes are retained, but commit hashes necessarily differ. Manuscript sources,
private reviewer files, correspondence, private source paths and hashes, and
internal release artifacts were removed from every published revision. A small
number of authentic commit messages may therefore refer to work whose private
files are intentionally absent. The final released inventory is bound by
`MANIFEST.json`.

## Evidence map

- `docs/methodology.md`: original pilot questions, narrowing decision, and final
  paper questions.
- `docs/pilot-protocol.md`: frozen pre-generation protocol.
- `docs/decisions.md`: chronological decisions and amendments.
- `experiment/`: frozen task, prompt, retrieval-packet, and schema definitions.
- `data/generated-trajectories/`: privacy-filtered run records, hash-bound
  prompt omission records, first responses, event streams, and stderr logs.
- `data/processed/`: structural and reuse analysis tables.
- `results/pilot/`: functional, reuse, agreement, adjudication, replication,
  and anonymous practitioner summaries.
- `analysis/`: interpretation boundaries and paper-facing findings.
- `scripts/` and `tests/`: validation and analysis implementation.
- `MANIFEST.json`: complete file inventory, public hashes, original-source
  hashes for transformed files, and release limitations.

## Quick verification

Python 3.9 or later is sufficient for core verification:

```bash
make check
make evidence-check
```

`make check` validates the tracked protocol, analysis code, and tests. `make
evidence-check` additionally requires the complete packaged inventory of 44 run
records, 147 prompt omission records and first responses, 147 event streams and
stderr logs, and six functional reports.

Functional retesting additionally requires Docker and a separately obtained
checkout of SR-Eval at commit
`6cf948d69427687bf61042640223d5b318f7bc4c`. Structural analysis and private
review import have pinned optional dependencies in `pyproject.toml`.

## Prompt reconstruction

SR-Eval and MRG-Bench do not state a redistribution license. Their authored
task instructions and the rendered prompts that contain them are therefore not
copied into this repository. Each omission record preserves the original
SHA-256 digest. After separately obtaining SR-Eval at the pinned commit, verify
and reconstruct the exact prompts locally with:

```bash
python3 scripts/reconstruct_prompts.py \
  --sr-eval .cache/SR-Eval \
  --output reconstructed-prompts
```

The reconstructed directory is ignored by Git and must not be committed here.

## Privacy transformations

Provider session/thread identifiers are replaced by deterministic public
pseudonyms. Email addresses embedded in upstream source comments are replaced
by deterministic redaction labels. Reviewer workbook paths and hashes are
removed from the public practitioner tables. The manifest records the original
private-source SHA-256 whenever a released file was transformed.

## Interpretation boundary

The evidence supports a transparent exploratory study, not a population-level
estimate of model quality or a general causal retrieval effect. Turns within a
trajectory are dependent, Pilot B is targeted and outcome-informed, Pilot C is
a two-task boundary check, and practitioner judgments are purposive descriptive
validation.

See `artifacts/SUBMISSION_ARTIFACT_README.md` for package verification,
exclusions, and release status.

## Licensing

The Apache-2.0 license applies only to study-authored material as defined in
`LICENSE_SCOPE.md`. Third-party and evidence material is documented in
`THIRD_PARTY_LICENSES.md` and is not relicensed by the study author.
