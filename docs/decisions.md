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

## 2026-09-04 — Pre-generation replacement of `between`

Exclude SR-Eval task `895990b3a5c56f093bdb72e6` (`between`) after its pinned
reference trajectory failed 5 of 10 cumulative checks in the smoke test. This
is a genuine cross-turn inconsistency: turn 1 requires a placeholder return of
`0.0`, later turns require computed cosine similarity, and turn 4 restores
exception messages that contradict turns 2 and 3. The same-turn checks all
passed, ruling out the container, build, and line-range mechanisms.

Replace it before any model generation with four-turn Java task
`6f8e8f1f18bd0ff1f3419f91` (`copyToTarget`). It preserves the primary stratum,
turn count, and progressive structural profile. Keep the failed smoke report as
an ignored local artifact and record its aggregate result here so the exclusion
remains auditable.

## 2026-09-04 — Reference-screen eligibility

Apply the cumulative functional gate at checkpoint level. A trajectory remains
in the pilot when every same-turn reference check is executable, but any
checkpoint that fails one or more tests from turns `1..t` is ineligible for the
primary structural and reuse analyses. Report those failures as benchmark
cross-turn incompatibilities and retain them for the regression analysis. This
clarifies the earlier task-level smoke criterion and avoids replacing useful
trajectories with leftover tasks whose supplied tests do not exercise the target
method.

## 2026-09-04 — Pre-generation replacement of `stream`

Exclude SR-Eval task `cf95a66e04f941a76d4b3552` (`stream`) after all six
reference checks failed, including every same-turn check. The pinned Spring AI
module fails compilation because `OpenAiChatModel` calls a protected
`AssistantMessage` constructor, independently of the injected method and test.

Replace it before model generation with three-turn control task
`3311fcb30839fc3620dccd19` (`methodToProperty`). The replacement keeps the
control stratum and turn count and supplies directly targeted, progressively
extended tests. Its pre-generation screen passes all three same-turn checks and
four of six cumulative checks; the two incompatible earlier-turn checks are
retained as ineligible checkpoints under the eligibility rule above.

## 2026-09-04 — Final pre-generation reference screen

The final 18-task sample passes 167 of 176 cumulative reference checks. All 70
same-turn checks pass, so every selected trajectory is executable. Sixty-two of
70 checkpoints pass every test from turns `1..t` and are eligible for the
primary structural and reuse analyses.

The eight ineligible checkpoints are confined to five trajectories:
`nodeArrayMerge` checkpoint 5, `randomAccessScoreProvider` checkpoint 4,
`methodToProperty` checkpoints 2–3, `underlineToCamel` checkpoints 2–3, and
`loadDocuments` checkpoints 2–3. Their nine failed test executions are retained
for regression analysis. No model output was generated or inspected before
these decisions were frozen.

## 2026-09-04 — Pilot A execution interface

Freeze Pilot A batch `pilot-a-20260904T213806Z`. Execute each trajectory in a
fresh resumable Codex CLI 0.153.0 session with explicit model slug
`gpt-5.6-sol`, High reasoning, and automatic routing disabled. Deliver the
frozen system prompt using `model_instructions_file`, disable web search, and
use a read-only empty session directory so the model cannot inspect benchmark
solutions or tests. Record raw CLI events and the unmodified final response for
every turn. Do not retry a model response or provide test feedback.

## 2026-09-04 — Pilot A generation closed

Pilot A batch `pilot-a-20260904T213806Z` completed all 18 independent
trajectories and all 70 planned turns. Each run has a unique Codex session ID;
every turn has a raw response, one extracted Java code block, and a usage
record. No model response was retried. These batch invariants were checked
before generated code was functionally tested or its contents were inspected.

## 2026-09-04 — Pilot A cumulative functional evaluation complete

Execute all 176 planned tests across the 70 generated checkpoints in batch
`pilot-a-20260904T213806Z`. Sixty checks pass and 116 fail. Twenty-two
checkpoints are cumulatively correct, spanning nine of the 18 trajectories.
Twenty-seven of 70 same-turn checks pass. All run records now contain complete
per-test outcomes and no checkpoint has an unknown cumulative status.

These counts are the unfiltered generated-code results. Apply the separately
frozen reference-eligibility screen before selecting checkpoints for structural
or reuse analysis. No structural analysis or Pilot B generation had begun when
this functional result was recorded.
