# Pilot Protocol

Status: **Pilot A frozen**. Batch `pilot-a-20260904T213806Z` may begin under the
committed protocol. No LLM generations had been recorded at this freeze.

Pilot A uses Codex CLI 0.153.0 with explicit model slug `gpt-5.6-sol`, High
reasoning, automatic routing disabled, web search disabled, and a read-only
empty working directory. The frozen system prompt is supplied as the model
instructions file. Every task starts in a fresh resumable session.

## Purpose

The pilot validates the experimental pipeline, measurement sensitivity, and
task executability. It is not powered to establish broad model-performance
claims.

## Pilot A: natural evolution

Run the 18 tasks in `experiment/config/pilot-tasks.json` once with the baseline
prompt protocol. Twelve tasks are structurally rich primary cases; six are
controls with smaller or more focused changes. No reuse hints or task-specific
engineering advice may be added.

## Pilot B: guardrail pairs

Run these six preselected tasks a second time with the exact contents of
`experiment/prompts/engineering-guardrails.txt` appended to every turn:

- `loadDocuments`
- `mergeBeans`
- `ensureCapacity`
- `nodeArrayMerge`
- `randomAccessScoreProvider`
- `diff`

Each baseline and guardrail run must start in an independent fresh session from
the same repository state. Pilot B is paired by SR-Eval hash, not merely by
method name.

## Before generation

1. Run `make check`.
2. Prepare the pinned benchmark with `make prepare`.
3. Load and start a disposable Java environment container.
4. Run `make doctor` and `make tasks`.
5. Run `make smoke TASK=copyToTarget`.
6. If successful, run `make smoke-all`.
7. Record any benchmark failures in `docs/decisions.md` before replacements.
8. Freeze prompt SHA-256 hashes and the run-record schema.

The smoke test uses each turn's SR-Eval reference implementation. At checkpoint
`t`, it executes every test from turns `1..t`, one at a time, against that
checkpoint. This deliberately goes beyond SR-Eval's default current-turn-only
evaluation.

## Generation procedure

For each `(task, condition)`:

1. Create a fresh run ID and independent model session.
2. Record the product, displayed model, reasoning level, date/time, prompt
   hashes, benchmark commit, task hash, and condition.
3. On turn 1, provide the repository context and SR-Eval instruction using the
   frozen turn-1 template.
4. On later turns, provide the immediately preceding generated method and the
   new instruction using the frozen code-edit template.
5. In Pilot B only, append the fixed guardrail block to every turn.
6. Save the unmodified raw response and the extracted Java method.
7. Do not provide test output or retry within the first-pass run.
8. Evaluate current and prior tests, then compute structural measurements.

## Smoke-test pass criteria

A task is executable when every reference checkpoint passes its same-turn test
in the pinned Java environment. A checkpoint is eligible for primary analysis
only when it also passes every earlier test from turns `1..t`. The harness
reports `pass` when all cumulative checks pass, `partial` when only cross-turn
checks fail, and `fail` when a same-turn check fails. A failure triggers
diagnosis in this order:

1. environment/container problem;
2. dependency or build problem;
3. dataset line-range/test problem;
4. genuine inconsistency between a later reference solution and an earlier
   test.

Categories 2–3 can justify replacement when they prevent same-turn execution.
Category 4 makes the affected checkpoint ineligible but does not by itself
remove the trajectory. Every decision must be made without viewing an LLM
generation for that task.

## Pilot decision rules

After the pilot, assign one outcome:

- **GO**: enough cumulatively correct checkpoints exist, structural metrics vary
  meaningfully, and missed-reuse/guardrail judgments are operationalizable.
- **NARROW**: generic structural signals are weak but missed reuse produces a
  credible, repeatable signal; focus the paper on reuse under evolution.
- **PIVOT**: executability, correctness yield, or task scale prevents a
  defensible analysis.

Before evaluating outcomes, report:

- trajectory and checkpoint correctness yield;
- missingness by repository and turn;
- effect-size estimates with uncertainty rather than only significance;
- number of automated reuse candidates and manually confirmed events;
- guardrail adherence by rule and turn;
- whether downstream-effort variables show usable variation.
