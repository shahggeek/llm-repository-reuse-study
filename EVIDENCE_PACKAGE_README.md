# SANER 2027 reproducibility artifact

Package: `saner-2027-public-evidence-candidate-2026-10-05`  
Source commit: `4edede84445c9b2a9013303ade9a4a561b6c9a44`  
SR-Eval commit: `6cf948d69427687bf61042640223d5b318f7bc4c`

This privacy- and license-filtered public evidence candidate covers Pilots A, B, and C plus the
anonymous practitioner validation. It contains 44 run
records, 147 raw model turn outputs, and
24 anonymous practitioner case responses.

Start with `artifacts/SUBMISSION_ARTIFACT_README.md`. Verify every file against
`MANIFEST.json` and the archive against the adjacent `.sha256` file. Raw
returned practitioner workbooks, identity mappings, correspondence, manuscript
sources, local failure logs, and the benchmark clone are not included. Provider
session identifiers are pseudonymized. Benchmark-authored task instructions and
rendered prompts are omitted because SR-Eval and MRG-Bench do not state a
redistribution license. Their original hashes are retained, and
`scripts/reconstruct_prompts.py` verifies exact reconstruction after the user
separately obtains the pinned SR-Eval checkout.

Study-authored material is licensed as described in `LICENSE_SCOPE.md`.
Third-party and evidence material is governed by `THIRD_PARTY_LICENSES.md`.
This package is a verified candidate, not the final permanent deposit.
