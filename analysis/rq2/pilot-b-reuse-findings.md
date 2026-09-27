# Pilot B Reuse Findings

## Final outcome

Pilot B reuse review is complete, independently checked, and adjudicated. The
final labels cover all 23 new checkpoints that are both functionally correct
and reference-eligible. The ten reviewed baseline checkpoints for the same
six-task subset include the documented cross-pilot consistency correction to
`nodeArrayMerge` turn 1.

| Condition | Reviewed checkpoints | R1 | R2 | R3 | Missed-reuse checkpoints | Trajectories with missed reuse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 10 | 5 | 3 | 2 | 5 | 2 |
| Guardrails only | 9 | 5 | 3 | 1 | 4 | 1 |
| Guardrails + retrieval | 14 | 14 | 0 | 0 | 0 | 0 |

These rows have different functional denominators and must not be compared as
independent rates. The primary inferential unit is the trajectory lineage;
turns are repeated dependent observations within a lineage.

## Independent-review reliability

The focused blinded validation contains 20 implementations in ten paired
cases. Condition names, A/B mappings, and primary labels were concealed. Exact
prompt context remained visible because context availability was itself a
reviewed construct.

- exact R0–R3 agreement: 19/20 (95%);
- linearly weighted R0–R3 Cohen's κ: 0.903;
- binary R2/R3 missed-reuse agreement: 20/20 (100%);
- exact C0–C3 agreement: 19/20 (95%); and
- linearly weighted C0–C3 Cohen's κ: 0.953.

The two disagreements were adjudicated without overwriting either raw review.
`PB-RV-106 B` is R3/C1: its guardrails-only implementation completely
rebuilds the insertion path, while `System.arraycopy()` is only a low-level
mechanism rather than partial reuse of `addInOrder()`. `PB-RV-110 B` remains
R3/C2: the visible `ArrayUtil` import is an indirect growth-abstraction cue,
although `growArrays()` is not explicit. The latter disagreement exposes a
minor C1/C2 boundary instability but does not affect missed-reuse agreement.

## Paired treatment evidence

Nine checkpoints are functionally correct in both new conditions. Their final
reuse transitions are:

- five R1 → R1 checkpoints;
- three R2 → R1 checkpoints; and
- one R3 → R1 checkpoint.

All four improvements belong to the `nodeArrayMerge` lineage. Under guardrails
only, its sequence is R3, R2, R2, R2 at C1: the generated code directly manages
`nodes`, `scores`, and `size`, with later turns reusing `IntHashSet` while still
duplicating insertion. Under retrieval, all four turns are R1/C3 and delegate
accepted insertions to the explicitly supplied `NodeArray.addInOrder()`.

Across the four clean paired lineages, one lineage improves
(`nodeArrayMerge`), three remain appropriately reused (`loadDocuments`,
`addInOrder` at the shared turn, and `ensureCapacity`), and none worsens. This
lineage view prevents four dependent `nodeArrayMerge` turns from being treated
as four independent replications.

Five additional checkpoints are correct only under retrieval relative to
guardrails: `addInOrder` turn 1 is R1/C3 and calls `growArrays()`, while `diff`
turns 1–4 are R1/C3 and delegate per-constraint semantics to
`ConstraintAnalysis.diff(...)`. Relative to baseline, retrieval changes
`addInOrder` turn 1 from R3/C2 to R1/C3 and changes all four `nodeArrayMerge`
turns from missed reuse to R1/C3.

## Why guardrails alone do not help

On the nine checkpoints correct in both baseline and guardrails-only
conditions, five remain R1 and the `nodeArrayMerge` lineage remains on a
missed-reuse path. An instruction to inspect and reuse repository abstractions
cannot reveal an API absent from both the prompt and the empty read-only
session directory. This supports the distinction between generic advice and
actual repository knowledge.

## Incomplete-context counterexample

`randomAccessScoreProvider` has no functionally correct checkpoint in either
new condition and is excluded from the R0–R3 denominator. Every generated
checkpoint fails compilation after calling the nonexistent
`SearchScoreProvider.exact(...)`.

The retrieval-supported code does adopt the supplied
`RandomAccessVectorValues.threadLocalSupplier()`, showing that the model used
the packet. However, the packet omits the necessary construction API,
`DefaultSearchScoreProvider.exact(...)`. The model fills that gap with a
plausible but nonexistent factory. This is evidence that retrieval completeness
matters, not that the model ignored complete explicit context.

## Supported claim

The combined Pilot A and Pilot B evidence supports a narrow mechanism claim:

> Engineering reminders alone do not resolve repository-level missed reuse
> when the relevant abstraction is absent. A small, explicit repository API
> packet can redirect a functionally correct evolution trajectory toward the
> repository abstraction, and that reuse choice can persist across later
> changes. The packet must cover the integration path; partial API context can
> still lead to plausible interface hallucination.

## Limitations and publication boundary

- Retrieval packets were selected after inspecting Pilot A outcomes.
- There is one run per task and condition.
- The focused validation sample was purposive, not randomly sampled.
- Exact prompt context made treatment content observable even though labels,
  condition names, and A/B mappings were concealed.
- Three rubric clarifications were supplied before submission and are recorded
  in the adjudication artifact.
- Functional and reuse gains are concentrated in a small number of tasks.

Do not report a general retrieval success rate or population-level causal
effect. Report the one improved paired lineage, the three unchanged-appropriate
lineages, the five retrieval-only correct checkpoints, and the incomplete
`randomAccessScoreProvider` counterexample.
