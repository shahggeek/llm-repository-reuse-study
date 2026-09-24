# Pilot A Reuse Feasibility Findings

## Outcome

Reuse is a credible direction, but the current evidence narrows the claim. The
pilot supports studying **repository-level missed reuse under limited context**;
it does not yet support saying that the model ignores visible reuse
opportunities.

The automated high-recall screen flagged 14 of 24 functionally correct
checkpoints because their reference implementation called at least one method
not called by the generated implementation. Ten checkpoints had no such call
difference. These are candidate counts, not confirmed defect counts.

A primary analyst and an independent blinded reviewer then examined one
checkpoint from each of the ten represented trajectories. Before adjudication,
they agreed on 9/10 exact R0–R3 labels (90%; linearly weighted Cohen's
κ = 0.889) and all 10 binary missed-reuse decisions (R2/R3 versus R0/R1).
They agreed on 8/10 context labels (80%; linearly weighted κ = 0.841).

Adjudication retained both original reviews and resolved one R0/R1 boundary
and two C1/C2 boundaries. The final calibration labels are:

| Class | Meaning | Checkpoints |
| --- | --- | ---: |
| R0 | No credible reuse opportunity | 0 |
| R1 | Appropriate reuse or acceptable equivalent | 6 |
| R2 | Partial reuse with meaningful duplication | 2 |
| R3 | Existing functionality reimplemented | 2 |

The four confirmed R2/R3 events occur in four different trajectories:
`addInOrder`, `encodeAnisotropic`, `invert`, and `nodeArrayMerge`. In every
For `addInOrder` and `invert`, the prompt contained indirect cues toward the
relevant abstraction family (C2), but did not name or show the applicable
helper. For `encodeAnisotropic` and `nodeArrayMerge`, the helper was wholly
latent (C1). No missed-reuse case had an explicit helper (C3). The experiment
used an empty read-only working directory, so the model could not inspect code
outside the prompt packet.

## What the evidence currently supports

- Functionally correct implementations can still bypass or reproduce
  repository-owned behavior.
- The R0–R3 rubric can distinguish acceptable alternative library use from
  repository-level duplication.
- Prompt context is likely a central mechanism: two missed-reuse cases involve
  latent helpers and two involve only indirect discoverability cues. None
  involves an explicitly available helper.
- The blinded calibration produced strong agreement on the substantive
  missed-reuse decision; remaining differences exposed narrow R0/R1 and C1/C2
  boundaries that are now clarified for the full review.
- Reference-only call differences are useful for triage but require manual
  review. For example, `ensureCapacity` uses a reasonable standard-library
  alternative, and the `addInOrder` turn-2 reference includes assertion-related
  behavior not yet required at that turn.

## What the evidence does not support yet

- A population-level rate of missed reuse. The sample is small, purposive, and
  contains dependent checkpoints.
- A claim that GPT-5.6 Sol disregards reuse despite explicit helper context.
  None of the R2/R3 cases had the applicable helper named or shown. The pilot
  does support the narrower observation that indirect cues were insufficient
  in two reviewed cases.
- A causal claim that more context improves reuse. That requires a controlled
  context or retrieval condition.
- A population-level reliability claim. Agreement is encouraging, but the
  calibration sample is small and purposive (n = 10).

## Consequence for Pilot B

The frozen guardrail asks the model to inspect repository context, but Pilot A
sessions ran in an empty directory and received only code above the target
function. Repeating that setup with advice alone cannot test whether access to
missing helpers improves reuse.

Before Pilot B generation, preserve the original guardrail pair as planned but
add an explicit design decision: either treat Pilot B narrowly as a **prompting
effect under fixed limited context**, or add a separately named
**retrieval-supported condition** that supplies candidate helper snippets or a
read-only repository checkout. Do not silently change the frozen two-condition
protocol.

## Next validation

1. Apply the clarified rubric to all 24 eligible correct checkpoints.
2. Preserve case-level evidence and report checkpoint and trajectory counts
   separately.
3. Freeze the final paper direction only after the full review.
