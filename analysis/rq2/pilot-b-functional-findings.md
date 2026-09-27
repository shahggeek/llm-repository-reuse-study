# Pilot B Functional Findings

## Outcome

Pilot B completed all 12 planned new trajectories and all 46 planned model
turns. Every trajectory used a distinct fresh session, no model response was
retried, and no test result was provided to the model during generation.

The table below applies the reference-eligibility decisions frozen before
Pilot A generation. It excludes `loadDocuments` checkpoints 2–3,
`nodeArrayMerge` checkpoint 5, and `randomAccessScoreProvider` checkpoint 4
identically in all three conditions.

| Task | Eligible checkpoints | Baseline correct | Guardrails correct | Guardrails + retrieval correct |
| --- | ---: | ---: | ---: | ---: |
| `loadDocuments` | 1 | 1 | 1 | 1 |
| `addInOrder` | 3 | 2 | 1 | 2 |
| `ensureCapacity` | 3 | 3 | 3 | 3 |
| `nodeArrayMerge` | 4 | 4 | 4 | 4 |
| `randomAccessScoreProvider` | 4 | 0 | 0 | 0 |
| `diff` | 4 | 0 | 0 | 4 |
| **Total** | **19** | **10** | **9** | **14** |

The corresponding eligible checkpoint/test-pair totals are 22/44 for the
baseline, 21/44 for guardrails only, and 32/44 for guardrails plus retrieval.
Raw totals before the frozen exclusions are:

| Condition | Passing checks | Cumulatively correct checkpoints |
| --- | ---: | ---: |
| Baseline | 28/58 | 10/23 |
| Guardrails only | 28/58 | 9/23 |
| Guardrails + retrieval | 39/58 | 14/23 |

## Paired contrasts

Guardrails alone do not improve aggregate functional correctness in this
six-task probe. Relative to the existing baseline, the eligible result changes
from 22 to 21 passing checks and from 10 to 9 cumulatively correct checkpoints.
The difference is confined to `addInOrder`; the other five task-level
cumulative results are unchanged.

Adding the bounded retrieval packet to the same guardrails increases the
eligible result by 11 passing checks and five cumulatively correct checkpoints.
This gain is concentrated in two tasks:

- `diff` changes from 0/4 to 4/4 cumulatively correct checkpoints and from
  0/10 to 10/10 passing checks.
- `addInOrder` changes from 1/3 to 2/3 cumulatively correct checkpoints and
  from 4/6 to 5/6 passing checks, restoring the existing baseline result.

The other four tasks show no functional change between the two new
conditions. In particular, `randomAccessScoreProvider` remains incorrect at
all eligible checkpoints despite retrieval.

## Interpretation boundary

These results establish functional eligibility for the next reuse review; they
do not yet show that the retrieved APIs caused appropriate reuse. The
retrieval candidates were selected after inspecting Pilot A outcomes, the
sample contains one run per task and condition, and checkpoints within a
trajectory are dependent. Report the changes as paired exploratory task
outcomes, not as a population-level causal effect or success rate.

The strongest functional contrast is task-specific: retrieval makes `diff`
fully correct. The next analysis must inspect whether the correct retrieval
outputs actually use the supplied repository abstractions and whether
`randomAccessScoreProvider` failed because of API use, missing integration
context, or an unrelated implementation error.

## Reuse analysis status

The R0–R3 review of all 23 new eligible correct checkpoints is complete. See
`analysis/rq2/pilot-b-reuse-findings.md` and
`results/pilot/pilot-b-reuse-final-summary.json`. The central paired result is
the four-turn `nodeArrayMerge` sequence changing from R3/R2/R2/R2 at C1 under
guardrails only to R1/R1/R1/R1 at C3 under retrieval, with functional
correctness held constant.
