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

## 2026-09-23 — Reuse rubric calibration

Retain the frozen R0–R3 reuse rubric and add an orthogonal C0–C3 context
availability code. A repository-level R2/R3 event is not attributed to the
model when the relevant abstraction was absent from the supplied context.

The high-recall call-difference screen flags 14/24 correct checkpoints for
manual review. A one-checkpoint-per-trajectory calibration sample contains one
R0, five R1, two R2, and two R3 classifications. All four provisional R2/R3
events are C1 (repository-only/latent), not explicit or discoverable in the
prompt. Therefore, treat reuse as a credible but not yet publication-ready
signal and frame the immediate hypothesis around context coverage.

Pilot A deliberately used an empty read-only working directory. Do not claim
that the model could inspect the full repository. Before Pilot B, decide
explicitly whether the frozen guardrail pair measures prompting under the same
limited context or whether a separately named retrieval-supported condition is
needed. Do not silently alter the frozen protocol.

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

## 2026-09-04 — Pilot A amendment replacements selected

Preserve the original Pilot A manifest and batch unchanged. Select two unused
SR-Eval tasks for a separate amendment after identifying supplied-signature
defects that confound every checkpoint of `copyToTarget` and `mergeBeans`.

Replace four-turn primary task `copyToTarget` with JVector task `rerank`
(`697f7351aaff39abd8dd4696`). Its evolving threshold, fallback, ranking, and
approximate-score requirements preserve the primary structural stratum. All 10
cumulative reference checks pass.

Replace three-turn reuse-sensitive control `mergeBeans` with JVector task
`addInOrder` (`892c3ff660b30a2824182053`). It has a stable signature and an
explicit opportunity to reuse `growArrays()` before adding an ordering
invariant, so it remains suitable for the Pilot B pair. All six cumulative
reference checks pass.

Reject Spring AI task `mergeOptions` (`9c74edf900020dff2741ee21`) after all six
reference checks fail compilation because the pinned module's tests import a
missing `EmbeddingOptionsBuilder`. No model output was generated for any
replacement during selection. The amendment remains selected but not generated.

## 2026-09-23 — Pilot A amendment execution frozen

Freeze amendment batch `pilot-a-amendment-20260923T012647Z` with two baseline
trajectories: four-turn `rerank` and three-turn `addInOrder`. Reuse the frozen
Pilot A model, reasoning effort, prompts, system instructions, read-only
sandbox, no-feedback rule, and one-run-per-task policy. Pin the amendment to the
SHA-256 digest of `experiment/config/protocol.json` so later protocol edits
cannot silently change this batch.

Keep amendment task packets, isolated Codex sessions, raw generations, and the
functional report in amendment-specific directories. Refuse to overwrite an
existing run. Use Codex CLI 0.153.0, matching the original Pilot A execution
interface; stage that exact version locally because the desktop-bundled CLI has
advanced to 0.153.1. No amendment model output had been generated when this
execution configuration was frozen.

## 2026-09-23 — Pilot A amendment closed and functional gate passed

Close amendment batch `pilot-a-amendment-20260923T012647Z` after generating all
seven planned turns in two unique, fresh Codex sessions. No model response was
retried and no test feedback was provided. Preserve one failed startup trace
under `work/infrastructure-failures`; it occurred before model contact because
the Codex state database was initially read-only and therefore qualifies as an
infrastructure retry under the frozen protocol.

The amendment passes 5 of 16 cumulative checks and produces 2 of 7
cumulatively correct checkpoints. `rerank` fails all ten checks because its
generated implementations do not compile against the pinned repository APIs.
`addInOrder` passes checkpoints 1 and 2; checkpoint 3 preserves the earlier
tests but fails its new ordering-validation test at runtime.

Substituting these two runs for `copyToTarget` and `mergeBeans` yields 65 of 176
passed checks, 24 of 70 cumulatively correct checkpoints, 29 of 70 passed
same-turn checks, and 10 of 18 trajectories with at least one correct
checkpoint. After the eight frozen reference-ineligible checkpoints and
prompt-confounded `set` checkpoint 1 are removed, the primary pool contains 61
eligible checkpoints and 151 checks. Twenty-four checkpoints across ten
trajectories are cumulatively correct and eligible for structural/reuse
analysis.

The functional gate outcome is **PROCEED**: begin structural measurement and
reuse-feasibility analysis on those 24 checkpoints. Do not yet assign the final
GO/NARROW/PIVOT outcome; the frozen decision rule also requires evidence that
structural metrics vary meaningfully and missed-reuse judgments are
operationalizable.

## 2026-09-23 — Post-generation prompt-context sufficiency audit

Audit all 18 adjusted Pilot A tasks after the `rerank` compilation result
revealed that its exact repository signature was not present in the supplied
prompt. Use a four-level rubric: explicit-consistent, inferable-consistent,
partially-conflicting, and underspecified integration types.

Classify 13 tasks as explicit-consistent and three as inferable-consistent.
Retain the already known `set` turn-1 signature conflict. Classify `rerank` as
underspecified because `ScoreFunction.ExactScoreFunction`, `NodesUnsorted`, and
the `GraphSearcher` caller contract are absent from both its instruction and
supplied context.

Because outcomes were known before this audit, do not replace the frozen
primary result or rerun any task. Add two post-generation sensitivity views.
Excluding only the four `rerank` checkpoints changes correctness yield from
24/61 (39.3%) to 24/57 (42.1%). A stricter literal-signature-only view yields
16/44 (36.4%). The conclusion is stable across the 36.4%–42.1% range, and the
24-checkpoint structural pool is unchanged by the clear-case exclusion.

For later model runs, require a literal repository-compatible signature before
generation. Before publication, obtain a second human review of the three
inferable-consistent classifications.

## 2026-09-23 — Pilot A structural extraction complete

Measure 24 eligible, cumulatively correct generated/reference checkpoint pairs
across ten trajectories. Retain a strict literal-signature subgroup of 16 pairs
across eight trajectories. Parse every method with pinned Tree-sitter Java and
independently validate cyclomatic complexity with pinned Lizard; all 48 methods
parse and all 48 complexity values agree.

Use descriptive paired metrics and deterministic 5,000-resample percentile
intervals clustered by trajectory. Median generated overhead is +1 nonblank
source line, 0 cyclomatic complexity, 0 approximate cognitive complexity, 0
nesting depth, and 0 local variables. Intervals are broad and generally include
zero. The strict subgroup gives the same qualitative result.

Conclude that the measurement pipeline is operational and detects strong
task-level heterogeneity, but generic aggregate structural overhead is weak in
this pilot. Keep the final GO/NARROW/PIVOT decision pending the missed-reuse
analysis. If reuse is credible, prefer NARROW over a broad structural-quality
claim.
