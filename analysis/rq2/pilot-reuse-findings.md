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

A single-analyst calibration review then examined one checkpoint from each of
the ten represented trajectories:

| Class | Meaning | Checkpoints |
| --- | --- | ---: |
| R0 | No credible reuse opportunity | 1 |
| R1 | Appropriate reuse or acceptable equivalent | 5 |
| R2 | Partial reuse with meaningful duplication | 2 |
| R3 | Existing functionality reimplemented | 2 |

The four provisional R2/R3 events occur in four different trajectories:
`addInOrder`, `encodeAnisotropic`, `invert`, and `nodeArrayMerge`. In every
case, the relevant helper was absent from the model's supplied prompt context.
The experiment used an empty read-only working directory, so the model could
not discover code outside the prompt packet.

## What the evidence currently supports

- Functionally correct implementations can still bypass or reproduce
  repository-owned behavior.
- The R0–R3 rubric can distinguish acceptable alternative library use from
  repository-level duplication.
- Prompt context is likely a central mechanism: all provisional missed-reuse
  cases in the calibration sample involve latent repository helpers.
- Reference-only call differences are useful for triage but require manual
  review. For example, `ensureCapacity` uses a reasonable standard-library
  alternative, and the `addInOrder` turn-2 reference includes assertion-related
  behavior not yet required at that turn.

## What the evidence does not support yet

- A population-level rate of missed reuse. The sample is small, purposive, and
  contains dependent checkpoints.
- A claim that GPT-5.6 Sol disregards reuse despite adequate context. None of
  the provisional R2/R3 cases had the relevant helper explicitly available.
- A causal claim that more context improves reuse. That requires a controlled
  context or retrieval condition.
- A publication-ready reliability claim. The calibration review was not
  independent or blinded.

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

1. Independently classify a blinded stratified subset and calculate agreement.
2. Review all 24 correct checkpoints after the rubric is stable.
3. Report checkpoint and trajectory counts separately.
4. Freeze the final paper direction only after the full review.
