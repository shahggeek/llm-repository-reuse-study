# LLM Evolution Quality Study

Research code and experimental artifacts for studying structural quality, reuse,
constraint adherence, and downstream maintenance effort in LLM-generated Java
code under progressive requirement refinement.

The pilot extends the public [SR-Eval](https://github.com/AjaxZhan/SR-Eval)
Java repository-level benchmark. SR-Eval supplies progressive requirements,
turn-specific reference solutions, tests, and repository environments. This
repository adds a frozen pilot sample, cumulative functional checks,
reference-normalized structural analysis, missed-reuse review, and a small
paired guardrail experiment.

## Pilot at a glance

- Benchmark: SR-Eval Java repository tasks, pinned to commit
  `6cf948d69427687bf61042640223d5b318f7bc4c`
- Pilot A: 18 trajectories (12 structurally rich tasks and 6 controls)
- Pilot B: 6 reuse-sensitive trajectories, paired baseline vs. guardrails
- Model: GPT-5.6 Sol, High reasoning, Auto routing disabled
- Replications: one independent run per condition during the methodology pilot
- Functional gate: each checkpoint must pass its current and all earlier tests
- Generated code is retained even when it fails; functional status determines
  which analyses it enters

The full rationale and predeclared decision rules are in
[`docs/pilot-protocol.md`](docs/pilot-protocol.md). The decision history is in
[`docs/decisions.md`](docs/decisions.md).

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

Raw generations, local benchmark checkouts, database files, Docker archives,
and smoke-test logs are ignored by Git. Small derived tables intended for the
paper may be committed after review.

## Quick start

Prerequisites: Python 3.12+, Docker, Maven (inside the SR-Eval image), and enough
disk space for the benchmark's Java environment. The bootstrap target installs
pinned Git LFS and `uv` binaries locally under the ignored `.tools/` directory.

```bash
make bootstrap
make check
make prepare
make doctor
make tasks
make smoke-dry-run
```

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
