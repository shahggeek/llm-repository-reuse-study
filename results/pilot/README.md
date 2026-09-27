# Pilot results

Pilot summaries and reviewed figures belong here. Raw smoke-test logs are saved
under `smoke-tests/` and ignored by Git.

`pilot-a-adjusted-functional-summary.json` is the durable clean analysis view.
It substitutes the frozen amendment runs for the two prompt-confounded original
trajectories, applies all checkpoint-level exclusions, and records the
functional decision to proceed to structural and reuse-feasibility analysis.

`prompt-context-sufficiency-audit.json` records the post-generation audit of all
18 adjusted tasks. The adjusted functional summary retains the frozen primary
view and adds clear-case and strict signature sensitivity results.

`pilot-a-structural-summary.json` contains paired descriptive distributions and
trajectory-clustered bootstrap intervals for the 24 eligible correct
checkpoints and the strict 16-checkpoint subgroup.

`pilot-a-reuse-screen-summary.json` summarizes the automated high-recall reuse
candidate screen. `pilot-a-reuse-rubric-pilot.json` records the provisional
single-analyst calibration review.

`pilot-a-reuse-blind-key.json` is the concealed A/B mapping for the independent
review workbook. The review is complete; retain the concealment warning for
future replications.

`pilot-a-reuse-reviewer2-responses.csv` preserves the completed Review sheet,
and `pilot-a-reuse-reviewer2-submission.json` records the source workbook hash.
`pilot-a-reuse-review-agreement.json` contains the pre-adjudication agreement
statistics and case comparisons. `pilot-a-reuse-adjudication.json` records the
three resolution decisions without overwriting either review.

`pilot-a-reuse-full-review-summary.json` summarizes the completed manual review
of all 24 eligible correct checkpoints, including class counts, context counts,
trajectory dependence, call-difference screen performance, and the documented
`ensureCapacity` prompt-provenance correction. The separate
`pilot-a-reuse-consistency-correction.json` records why baseline
`nodeArrayMerge` turn 1 was changed from R2/C1 to R3/C1 after the same rubric
boundary was independently adjudicated in Pilot B.

`pilot-b-functional-summary.json` is the durable three-condition functional
view for the six Pilot B tasks. It records generation integrity, raw outcomes,
the primary reference-eligible outcomes, paired condition deltas, and hashes of
the ignored run records and functional reports used to build the summary.

`pilot-b-reuse-summary.json` validates and summarizes the primary reuse review
of all 23 new eligible correct Pilot B checkpoints. It includes condition-level
R/C counts, paired checkpoint transitions, the `randomAccessScoreProvider`
context-gap diagnosis, and source-artifact hashes.

`pilot-b-reuse-reviewer2-responses.csv` and
`pilot-b-reuse-reviewer2-submission.json` preserve the returned focused review
and workbook hash. `pilot-b-reuse-review-agreement.json` freezes the
pre-adjudication reliability statistics. `pilot-b-reuse-adjudication.json`
records both disagreements and final decisions without replacing raw labels.
`pilot-b-reuse-final-summary.json` is the paper-facing adjudicated result,
including checkpoint transitions and lineage-level interpretation.

`industry-expert-review-package.json` freezes the six-case practical validation
package, including workbook and instruction hashes. The reviewer-facing files
are under `outputs/industry-expert-review/`. Keep
`industry-expert-review-blind-key.json` concealed until all planned expert
responses are frozen.
