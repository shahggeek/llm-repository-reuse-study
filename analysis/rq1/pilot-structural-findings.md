# Pilot A structural findings

Status: descriptive pilot result; not a population-level model comparison.

## Dataset and validation

- 24 eligible, cumulatively correct generated/reference checkpoint pairs from
  10 trajectories.
- Strict literal-signature subgroup: 16 pairs from eight trajectories.
- All 48 method snippets parsed without errors.
- Tree-sitter and Lizard independently produced identical cyclomatic
  complexity for all 48 methods.
- Uncertainty intervals use 5,000 deterministic bootstrap resamples clustered
  by trajectory.

## Main paired results

Positive overhead means the generated method is structurally larger or more
complex than the same-turn SR-Eval reference.

| Metric | Generated median | Reference median | Median paired overhead | Generated higher / equal / lower | Clustered 95% interval for median overhead |
|---|---:|---:|---:|---:|---:|
| Nonblank, noncomment source lines | 13 | 14 | +1 | 13 / 2 / 9 | [-1, 9] |
| Statements | 8 | 8 | +0.5 | 12 / 4 / 8 | [-1, 6] |
| Cyclomatic complexity | 4 | 4 | 0 | 9 / 8 / 7 | [-1, 2] |
| Cognitive complexity approximation | 5.5 | 5 | 0 | 10 / 5 / 9 | [-2.5, 3] |
| Maximum control nesting | 2 | 2 | 0 | 4 / 9 / 11 | [-1, 0] |
| Method invocations | 3.5 | 4 | 0 | 6 / 11 / 7 | [-2, 1] |
| Local variables | 2 | 2 | 0 | 11 / 10 / 3 | [0, 3] |

The aggregate pattern is mixed. Generated methods are more often slightly
longer and use more local variables, but median complexity, nesting, and call
overheads are zero. Every clustered interval includes zero except the local
variable interval, whose lower bound is zero. The pilot therefore does not
support a broad claim that correct model code is uniformly more complex than
the benchmark reference.

## Heterogeneity

Task-level patterns vary substantially:

- `invert` grows progressively larger than its reference, reaching +17 source
  lines and +3 cyclomatic complexity at turn 4.
- `encodeAnisotropic` is +17 and +22 source lines at its two correct turns.
- `nodeArrayMerge` is much shorter than its increasingly elaborate reference
  at turns 2–4 (-31, -31, and -50 source lines) while remaining functionally
  correct under the eligible tests.
- `calculatePhaseTimeGradient`, `loadDocuments`, and parts of `ensureCapacity`
  remain close to or smaller than their references.

This heterogeneity explains why paired medians and means point in different
directions. It also suggests that reference implementation style and task
family are important moderators. With only ten contributing trajectories, the
pilot should show task-level distributions instead of presenting one pooled
average as the principal finding.

## Strict-signature robustness

The strict 16-pair subgroup gives the same broad conclusion:

- median source-line overhead: +1, clustered interval [-8, 4];
- median cyclomatic overhead: 0, interval [-1, 1];
- median cognitive overhead: -0.5, interval [-3.5, 1];
- median nesting overhead: 0, interval [-1, 0];
- median local-variable overhead: 0, interval [0, 3].

The result is therefore not driven by the three inferable-signature tasks.

## Interpretation for the pilot decision

The structural extractor is operational and sensitive to meaningful
within-task differences, but generic aggregate structural overhead is weak and
uncertain. This does not yet justify **GO** for a broad structural-quality
paper. The next decision point is the RQ2 reuse analysis:

- if missed reuse is credible and repeatable, select **NARROW** and center the
  paper on reuse and repository integration under progressive evolution;
- if reuse judgments are also weak or unreliable, select **PIVOT**;
- retain **GO** only if later task-level structural/reuse evidence is stronger
  than the pooled pilot medians suggest.

Cross-turn medians are not interpreted as evolution trends because the set of
functionally correct tasks changes by turn. Within-trajectory evolution and
downstream consequences should be analyzed instead.
