# Pilot B Reuse Findings

## Outcome

The primary Pilot B review applies the calibrated R0–R3/C0–C3 rubric to all
23 new checkpoints that are both functionally correct and reference-eligible.
The existing ten reviewed baseline checkpoints for the same six-task subset
are reused unchanged.

| Condition | Reviewed checkpoints | R1 | R2 | R3 | Missed-reuse checkpoints | Trajectories with missed reuse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 10 | 5 | 4 | 1 | 5 | 2 |
| Guardrails only | 9 | 5 | 4 | 0 | 4 | 1 |
| Guardrails + retrieval | 14 | 14 | 0 | 0 | 0 | 0 |

These rows have different functional denominators and must not be compared as
independent rates. The paired checkpoint transitions provide the more useful
mechanism evidence.

## Paired treatment evidence

Nine checkpoints are functionally correct in both new conditions. Their reuse
transitions are:

- five R1 → R1 checkpoints; and
- four R2 → R1 checkpoints, all from `nodeArrayMerge` turns 1–4.

The four `nodeArrayMerge` transitions simultaneously change from C1 to C3.
Under guardrails only, the relevant insertion helper is absent from the prompt,
and the generated code directly mutates `nodes`, `scores`, and `size`. Under
retrieval, the packet explicitly supplies `NodeArray.addInOrder()` and
`NodeArray.size()`, and every correct evolved implementation delegates accepted
insertions to `addInOrder()`.

This is the cleanest Pilot B mechanism result because functional correctness is
constant: all four checkpoints are correct in both conditions, while the reuse
path changes from duplicated insertion behavior to the repository abstraction.
The reuse improvement also persists through all four evolution turns.

Five additional checkpoints are correct only under retrieval relative to
guardrails:

- `addInOrder` turn 1 is R1/C3 and calls the explicitly supplied
  `growArrays()`; and
- `diff` turns 1–4 are R1/C3 and consistently delegate per-constraint semantics
  to the explicitly supplied `ConstraintAnalysis.diff(...)`.

Compared with the existing baseline on the ten checkpoints correct in both
conditions, retrieval changes one `addInOrder` checkpoint from R3/C2 to R1/C3,
changes four `nodeArrayMerge` checkpoints from R2/C1 to R1/C3, and leaves five
R1 checkpoints at R1. There is no paired appropriate-to-missed regression.

## Why guardrails alone do not help

On the nine checkpoints correct in both the baseline and guardrails-only
conditions, five remain R1 and all four `nodeArrayMerge` checkpoints remain R2.
The text instruction to inspect and reuse repository abstractions cannot reveal
an API that is absent from both the supplied prompt and the empty read-only
session directory. This supports the distinction between advice and actual
repository knowledge.

## Incomplete-context counterexample

`randomAccessScoreProvider` has no functionally correct checkpoint in either
new condition and is therefore excluded from the R0–R3 denominator. Every
generated checkpoint fails compilation after calling the nonexistent
`SearchScoreProvider.exact(...)`.

The retrieval-supported code does adopt the supplied
`RandomAccessVectorValues.threadLocalSupplier()`, showing that the model used
the packet. However, the packet omits the necessary construction API,
`DefaultSearchScoreProvider.exact(...)`. The model fills that gap with a
plausible but nonexistent factory. This is evidence that retrieval completeness
matters; it is not evidence that the model ignored complete explicit context.

## Supported claim

The combined Pilot A and Pilot B evidence supports a narrow mechanism claim:

> Engineering reminders alone do not resolve repository-level missed reuse
> when the relevant abstraction is absent. A small, explicit repository API
> packet can redirect a functionally correct evolution trajectory toward the
> repository abstraction, and that reuse choice can persist across later
> changes. The packet must cover the integration path; partial API context can
> still lead to plausible interface hallucination.

This wording is stronger than the Pilot A context hypothesis but remains
task-specific and exploratory.

## Limitations and publication boundary

- Retrieval packets were selected after inspecting Pilot A outcomes.
- There is one run per task and condition.
- Checkpoints within a trajectory are dependent observations.
- The functional and reuse gains are concentrated in a small number of tasks.
- The Pilot B primary analyst knew the treatment condition. The R0–R3 rubric
  was independently calibrated during Pilot A, but the Pilot B transition
  labels have not yet received a new blinded check.

Do not report a general retrieval success rate or population-level causal
effect. Report paired task/checkpoint transitions, especially the four
`nodeArrayMerge` R2/C1 → R1/C3 transitions, alongside the incomplete
`randomAccessScoreProvider` counterexample.
