# Pilot A Reuse Findings

## Outcome

Pilot A supports a **NARROW** paper direction centered on repository-level
reuse under limited context. Functionally correct generated code sometimes
reproduces or bypasses existing repository behavior, and that choice can
persist through later evolution turns. The pilot does not support a broad
claim that the model ignores helpers that are explicitly supplied.

The complete manual review covers all 24 eligible correct checkpoints from ten
trajectories and four repositories:

| Class | Meaning | Checkpoints |
| --- | --- | ---: |
| R0 | No credible reuse opportunity | 0 |
| R1 | Appropriate reuse or acceptable equivalent | 13 |
| R2 | Partial reuse with meaningful duplication | 7 |
| R3 | Existing functionality reimplemented | 4 |

Eleven of 24 checkpoint observations are R2/R3. They are not independent
events: all 11 occur within four trajectories.

| Trajectory | Reviewed checkpoints | R2/R3 checkpoints | Pattern |
| --- | ---: | ---: | --- |
| `addInOrder` | 2 | 1 | R3 → R1 |
| `encodeAnisotropic` | 2 | 2 | R3 → R3 |
| `invert` | 4 | 4 | R2 → R2 → R2 → R2 |
| `nodeArrayMerge` | 4 | 4 | R3 → R2 → R2 → R2 |

The other six trajectories contain 13 R1 checkpoints and no R2/R3 event.
Therefore, report both **11/24 checkpoints** and **4/10 trajectories**; do not
treat the 24 checkpoints as independent observations.

## Context availability

Among the 11 R2/R3 checkpoints:

- six are C1: the applicable repository helper is absent from the model's
  supplied context (`encodeAnisotropic` and `nodeArrayMerge`);
- five are C2: imports, types, or repository conventions indirectly suggest
  the relevant abstraction family (`addInOrder` and `invert`); and
- zero are C3: no missed-reuse checkpoint explicitly names or shows the
  applicable helper.

This supports two related observations. Missing repository context is a
plausible mechanism, and indirect cues alone may not be sufficient to produce
repository-aligned reuse. A causal claim requires a controlled
retrieval-supported condition.

## Calibration reliability

Before the full review, a primary analyst and a second blinded reviewer
classified one generated checkpoint from each trajectory. The second blinded
reviewer had substantial professional software-development experience
specializing in Java. Pre-adjudication
agreement was:

- 9/10 exact R0–R3 labels (90%);
- linearly weighted Cohen's κ = 0.889;
- 10/10 binary R2/R3 versus R0/R1 decisions (100%);
- 8/10 exact C0–C3 labels (80%); and
- linearly weighted context κ = 0.841.

The full review retains the raw reviewer responses and separate adjudication
record. All four missed-reuse decisions in the calibration sample were
independently confirmed.

One prompt-provenance correction was found while reviewing exact trajectory
history. `ensureCapacity` turn 2 explicitly included `ArrayUtil.grow()` in the
previous generated method, so its full-review context label is C3 rather than
C2. The blinded packet exposed the initial context slice, not the prior
generated method. The checkpoint remains R1, so this correction changes no
missed-reuse result or pre-adjudication agreement statistic.

## Automated screen

The high-recall call-difference screen flagged 14 of 24 checkpoints. Manual
review confirmed 11 as R2/R3 and rejected three as acceptable alternatives or
turn-specific differences. All ten unflagged checkpoints were R1.

On this purposive reviewed pool, the screen therefore has 11 true positives,
three false positives, ten true negatives, and no false negatives. Its 78.6%
precision and 100% recall are descriptive triage results, not external
validation estimates.

## What the evidence supports

- Functionally correct implementations can still bypass or reproduce
  repository-owned behavior.
- An initial reuse choice can persist through later evolution turns:
  `encodeAnisotropic`, `invert`, and `nodeArrayMerge` retain R2/R3 at every
  reviewed later correct checkpoint.
- The model corrected an initial reuse miss when the next `addInOrder`
  instruction explicitly named `growArrays()` (R3/C2 → R1/C3).
- Exact helper visibility appears important: missed reuse occurs with latent or
  indirect context, but not with explicit helper context in this pilot.
- Reference-only call differences are useful for triage but still require
  manual semantic review.

## What the evidence does not support

- A population-level missed-reuse rate. The pool is small, purposive, and
  contains dependent checkpoints.
- A claim that GPT-5.6 Sol ignores explicitly available helpers. No R2/R3
  checkpoint is C3.
- A causal claim that adding context fixes reuse. Pilot A has no randomized
  context or retrieval treatment.
- A population-level reliability estimate from the ten-case calibration.

## Consequence for Pilot B

The original guardrail asks the model to inspect repository context, but Pilot
A ran in empty read-only directories. Advice alone cannot reveal helpers that
are absent from the prompt. The next design decision should preserve the
frozen guardrail comparison and add a separately named retrieval-supported
condition, or explicitly limit Pilot B to a prompting effect under the same
restricted context.

Given the Pilot A result, a retrieval-supported condition is the more direct
test of the proposed mechanism. It should expose candidate helper declarations
or a read-only repository checkout without changing the original Pilot A data.
