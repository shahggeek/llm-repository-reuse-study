# Decision Log

This is an append-only research log. Amend a decision with a new dated entry;
do not silently rewrite earlier rationale after results are known.

## 2026-09-04 — Public-data boundary

Use public SR-Eval artifacts and study-generated data only. Employer code,
internal prompts, company framework implementations, and proprietary examples
are out of scope.

## 2026-09-04 — Benchmark and revision

Use SR-Eval's Java repository-level dataset at commit
`6cf948d69427687bf61042640223d5b318f7bc4c`. Do not vendor the benchmark. A local
ignored checkout is prepared from the pinned revision.

## 2026-09-04 — Pilot sample

Freeze 18 trajectories: 12 structurally rich primary cases and 6 controls. The
selection is keyed by SR-Eval `hash_id`, so overloaded method names cannot select
the wrong task. Replacement is allowed only for pre-generation executability
failures and must be logged before inspecting model output.

## 2026-09-04 — Model configuration

Use GPT-5.6 Sol with High reasoning and automatic model routing disabled. Use
one independent run per task/condition in the methodology pilot. Record the
exact displayed model and product/interface metadata for every run.

## 2026-09-04 — Prompting strategy

Use SR-Eval's base/generated-history code-edit strategy. Turn 1 receives
repository context plus the first instruction. Each later turn receives the
immediately preceding generated method plus the new instruction. No test
feedback or repair attempt is included in the first-pass trajectory.

## 2026-09-04 — Functional gate

Evaluate checkpoint `t` with all tests from turns `1..t`. Retain every output;
use cumulatively correct checkpoints for primary structural and reuse analyses.

## 2026-09-04 — Two-stage pilot

Pilot A measures natural structural overhead and missed reuse across all 18
tasks without added engineering guardrails. Pilot B repeats six preselected,
reuse-sensitive tasks with one identical frozen guardrail block. Human review is
discussed as an implication, not evaluated as a treatment.

## 2026-09-04 — Metrics

Report structural dimensions individually rather than constructing a composite
quality score. Compare each generated checkpoint to its same-turn SR-Eval
reference implementation and calculate absolute and normalized overhead.
