# Processed data

`pilot-a-structural-metrics.csv` is the flat paired metric table used for RQ1.
`pilot-a-structural-metrics.json` retains parser diagnostics, call targets,
smell flags, and nested overhead records. Both contain derived measurements and
code hashes, not raw generated or reference code.

`pilot-a-reuse-candidates.csv` and `.json` contain the reproducible,
high-recall method-call difference screen for the same 24 checkpoints. They are
triage artifacts; the candidate flags are not manual missed-reuse labels.

`pilot-a-reuse-full-review.csv` and `.json` contain the completed R0–R3 and
C0–C3 review of all 24 eligible correct checkpoints. The flat CSV includes
case evidence, context evidence, maintenance consequences, screen fields, and
generated/reference code hashes. Rebuild and validate the CSV and aggregate
summary with `make reuse-full-review`.

`pilot-b-reuse-review.csv` and `.json` contain the primary R0–R3/C0–C3 review
of all 23 new eligible correct Pilot B checkpoints across the guardrails-only
and guardrails-plus-retrieval conditions. The JSON is the human-authored review
record; the CSV is regenerated and validated by `make reuse-pilot-b`.

`pilot-b-reuse-review-adjudicated.csv` and `.json` preserve the final consensus
view after the focused independent review. They retain all primary records and
change only guardrails-only `nodeArrayMerge` turn 1 from R2 to R3, with an
explicit adjudication identifier. Rebuild them with `make reuse-pilot-b-final`.

Locally derived checkpoint-level tables belong here. Only small, reviewed,
de-identified research tables should be force-added to Git.
