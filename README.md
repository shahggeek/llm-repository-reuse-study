# LLM Evolution Quality Study

Private working repository for a study of repository-level reuse in
LLM-generated Java code under progressive requirement refinement. The final
paper asks when functionally correct implementations miss existing repository
abstractions, whether that choice persists, how bounded API context changes the
outcome in targeted tasks, and whether practitioners perceive the resulting
implementations differently.

The pilot extends the public [SR-Eval](https://github.com/AjaxZhan/SR-Eval)
Java repository-level benchmark. SR-Eval supplies progressive requirements,
turn-specific reference solutions, tests, and repository environments. This
repository adds a frozen pilot sample, cumulative functional checks,
reference-normalized structural screening, semantic missed-reuse review,
targeted guardrail/API-context probes, and blinded practitioner validation.

## Pilot at a glance

- Benchmark: SR-Eval Java repository tasks, pinned to commit
  `6cf948d69427687bf61042640223d5b318f7bc4c`
- Pilot A: 18 trajectories (12 structurally rich tasks and 6 controls)
- Pilot B: 6 reuse-sensitive trajectories across the existing baseline,
  guardrails-only, and guardrails-plus-retrieval conditions
- Pilot C: 2 non-JVector repositories, 2 prompt conditions, and 3 independent
  repetitions per task/condition (12 new trajectories)
- Model: GPT-5.6 Sol, High reasoning, Auto routing disabled
- Replications: one per Pilot A/B cell; three per Pilot C task/condition cell
- Functional gate: each checkpoint must pass its current and all earlier tests
- Generated code is retained even when it fails; functional status determines
  which analyses it enters
- Final pilot decision: **NARROW** from generic structural quality to
  repository reuse, persistence, and explicit API context

The full rationale and predeclared decision rules are in
[`docs/pilot-protocol.md`](docs/pilot-protocol.md). The decision history is in
[`docs/decisions.md`](docs/decisions.md).

The completed clean functional view is in
[`results/pilot/pilot-a-adjusted-functional-summary.json`](results/pilot/pilot-a-adjusted-functional-summary.json).
The task-level prompt/context quality review is in
[`docs/prompt-context-audit.md`](docs/prompt-context-audit.md).
The first structural result is in
[`analysis/rq1/pilot-structural-findings.md`](analysis/rq1/pilot-structural-findings.md).
The cross-repository replication result is in
[`analysis/rq2/pilot-c-findings.md`](analysis/rq2/pilot-c-findings.md).
The frozen four-practitioner validation is summarized in
[`analysis/rq2/industry-expert-validation-findings.md`](analysis/rq2/industry-expert-validation-findings.md).

To resume the current research state after a break, start with
[`docs/resume-handoff.md`](docs/resume-handoff.md).

The SANER 2027 IEEE manuscript source is under [paper/](paper/). It is private
working material and must not be copied into the public evidence repository. Its
claim-to-evidence matrix is the control point for all paper-facing numbers and
interpretive claims.

## Private working repository versus public evidence

This repository contains manuscript and internal research-management material
and must remain private. `scripts/build_submission_artifact.py` creates a
privacy-filtered public evidence candidate using an explicit allowlist. The
public package excludes the manuscript, correspondence, raw returned
workbooks, reviewer-facing spreadsheets, machine-specific logs, and identity
mappings. It also pseudonymizes provider session identifiers and redacts email
addresses embedded in upstream source comments.

The public package uses scoped licensing. Apache-2.0 applies only to
study-authored material listed in `LICENSE_SCOPE.md`. Because SR-Eval and
MRG-Bench do not state a redistribution license, their authored task
instructions and rendered prompt text are omitted and can be reconstructed
locally from a separately obtained pinned checkout. See
`THIRD_PARTY_LICENSES.md` for attribution and exclusions.

## Repository layout

```text
analysis/                 RQ-specific analysis notebooks/scripts/results
data/                     generated trajectories and derived metric tables
docs/                     methodology, protocol, and decision log
environment/              benchmark and runtime setup notes
experiment/config/        frozen task manifest and protocol configuration
experiment/pilot-tasks/   task-selection documentation
experiment/prompts/       versioned baseline and guardrail prompts
experiment/schemas/       machine-readable run-record contract
results/                  pilot and full-study reports
scripts/                  validation, export, and smoke-test harness
tests/                    harness tests
```

Raw generations, task packets, local benchmark checkouts, database files,
Docker archives, and smoke-test logs are ignored by Git in this private working
repository. The public evidence package copies the required deidentified raw
generations, task packets, and functional reports and binds every packaged file
with SHA-256.

## Quick start

Prerequisites: Python 3.9+ for core verification, Docker, Maven (inside the
SR-Eval image), and enough
disk space for the benchmark's Java environment. The bootstrap target installs
pinned Git LFS and `uv` binaries locally under the ignored `.tools/` directory.
Core verification uses only the Python standard library. Optional dependency
groups and exact versions for Docker evaluation, structural analysis, and
private review-workbook import are recorded in `pyproject.toml`.

```bash
make bootstrap
make check
make prepare
make doctor
make tasks
make smoke-dry-run
```

`make check` is the clean-clone core verification. Tests requiring archived raw
evidence are reported as skipped when those ignored inputs are absent. Run
`make evidence-check` when the complete local or packaged evidence tree is
present; it fails if any expected trajectory or functional report is missing.

The `.mjs` workbook construction and extraction utilities use the workspace-
provided `@oai/artifact-tool` and are retained only in the private working
repository for provenance. They and the workbooks they process are excluded
from the public evidence package. Public verification starts from the frozen,
deidentified CSV/JSON review records.

`make prepare` clones the pinned SR-Eval revision into `.cache/SR-Eval`, fetches
the Java environment's Git LFS objects, and reconstructs its archive. It does
not load or start an image automatically. Follow
[`environment/README.md`](environment/README.md) to load the reconstructed image
and start a disposable container named `mrgbench_container_1`.

When the container is ready:

```bash
make smoke TASK=copyToTarget
```

Run all 18 reference trajectories only after the one-task smoke test succeeds:

```bash
make smoke-all
```

After the protocol is frozen and committed, generate one Pilot A trajectory:

```bash
make pilot-a TASK=copyToTarget
```

The runner starts a fresh isolated Codex session for each task, retains every
prompt, raw response, and event stream under the ignored
`data/generated-trajectories/` tree, and never retries a model response. Use
`make pilot-a-all` only after validating the first trajectory's records.

After generation closes, run the cumulative functional evaluation separately:

```bash
make test-pilot-a
```

This tests each generated checkpoint against its current and all earlier tests,
updates the ignored run record, and does not send test results back to the model.

The two-task Pilot A amendment is deliberately isolated from the original
manifest, raw trajectories, and test report. Prepare and verify it with:

```bash
make amendment-cli
make amendment-validate
make amendment-export
make amendment-preflight
make amendment-smoke-dry-run TASK=rerank
make amendment-smoke-dry-run TASK=addInOrder
```

After committing the frozen amendment configuration, generate both replacement
trajectories and then evaluate all 16 cumulative checks:

```bash
make pilot-a-amendment-all
make test-pilot-a-amendment
```

Pilot B is frozen separately so the historical Pilot A protocol hash remains
unchanged. Validate its three-condition design, exact task identities, prompt
hashes, literal target signatures, and bounded retrieval packets with:

```bash
make pilot-b-check
make pilot-b-preflight
```

Pilot B reuses the six existing baseline trajectories and requires 12 new
trajectories: six with engineering guardrails and six with the same guardrails
plus a short task-specific repository API packet. The frozen configuration is
[`experiment/config/pilot-b.json`](experiment/config/pilot-b.json).

The preflight renders all 46 turn-level prompt skeletons for the 12 planned new
trajectories, verifies the six existing baseline records, and confirms the
frozen Codex CLI version without contacting the model. After reviewing that
output, generate and evaluate one condition at a time:

```bash
make pilot-b-all PILOT_B_CONDITION=engineering-guardrails
make test-pilot-b PILOT_B_CONDITION=engineering-guardrails
make pilot-b-all PILOT_B_CONDITION=engineering-guardrails-retrieval
make test-pilot-b PILOT_B_CONDITION=engineering-guardrails-retrieval
```

Pilot C is a predeclared cross-repository replication on one LangChain4j case
and one Spring AI case. Both reference histories passed all six cumulative
smoke checks before selection was frozen. It generates three fresh runs under
each of two conditions, for 12 trajectories and 24 prompt turns:

```bash
make pilot-c-check
make pilot-c-preflight
make pilot-c-all PILOT_C_CONDITION=engineering-guardrails
make test-pilot-c PILOT_C_CONDITION=engineering-guardrails
make pilot-c-all PILOT_C_CONDITION=engineering-guardrails-retrieval
make test-pilot-c PILOT_C_CONDITION=engineering-guardrails-retrieval
```

The frozen configuration is
[`experiment/config/pilot-c.json`](experiment/config/pilot-c.json). Each
repetition uses a fresh session, receives no test feedback, and cannot be
retried after model contact.

Generate the validated structural metric table after functional selection:

```bash
make structural-pilot
```

Smoke reports use `pass` when every cumulative check succeeds, `partial` when
all same-turn checks execute but one or more earlier-turn checks conflict, and
`fail` when any same-turn reference check is not executable. `partial` exits
successfully while preserving the incompatible checkpoints in the report.

## Research boundaries

This study uses public benchmark data only. Do not add employer code, internal
prompts, company framework implementations, proprietary examples, credentials,
or other confidential material.

The repository is an early research artifact. Pilot decisions are frozen before
generation, but they may be amended for benchmark executability using the rules
recorded in the protocol and decision log.
