# Processed data

`pilot-a-structural-metrics.csv` is the flat paired metric table used for RQ1.
`pilot-a-structural-metrics.json` retains parser diagnostics, call targets,
smell flags, and nested overhead records. Both contain derived measurements and
code hashes, not raw generated or reference code.

`pilot-a-reuse-candidates.csv` and `.json` contain the reproducible,
high-recall method-call difference screen for the same 24 checkpoints. They are
triage artifacts; the candidate flags are not manual missed-reuse labels.

Locally derived checkpoint-level tables belong here. Only small, reviewed,
de-identified research tables should be force-added to Git.
