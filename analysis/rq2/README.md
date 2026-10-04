# Original Pilot RQ2 and final paper evidence — Repository reuse

This directory began as the original Pilot RQ2 workspace. After the NARROW
decision, repository reuse became the paper's main focus, so it also contains
evidence used by Paper RQ1--RQ4. The final question mapping is documented in
`../../docs/methodology.md`.

Current artifacts:

- `reuse-rubric.md`: operational R0–R3 and C0–C3 review rules.
- `industry-expert-validation-protocol.md`: blinded practical-validation
  protocol for human code-review and maintenance judgments.
- `industry-expert-validation-findings.md`: frozen four-reviewer descriptive
  results, control-case disagreements, themes, and interpretation boundary.
- `pilot-reuse-findings.md`: complete Pilot A reuse findings and NARROW
  decision.
- `blinded-review-protocol.md`: independent review and agreement procedure.
- The blinded A/B reviewer workbook is retained under
  `outputs/pilot-a-reuse-independent-review/` in the private working repository.
  Public evidence uses the extracted response CSV, source-workbook hash,
  agreement report, and adjudication record; the workbook itself is excluded.
- `../../data/processed/pilot-a-reuse-candidates.csv`: compact screen output.
- `../../data/processed/pilot-a-reuse-candidates.json`: complete screen evidence.
- `../../results/pilot/pilot-a-reuse-screen-summary.json`: aggregate screen.
- `../../results/pilot/pilot-a-reuse-rubric-pilot.json`: ten-trajectory manual
  calibration sample.
- `../../data/processed/pilot-a-reuse-full-review.csv` and `.json`: complete
  24-checkpoint manual evidence table.
- `../../results/pilot/pilot-a-reuse-full-review-summary.json`: aggregate
  checkpoint, trajectory, context, and screen results.

The independent calibration and complete Pilot A review are finished. Preserve
the raw reviewer submissions, agreement output, adjudication record, and
prompt-provenance correction as separate artifacts.

The industry-expert review is deliberately different from the rubric review:
experts judge approval, repository fit, maintainability, duplicated behavior,
and future-change risk rather than reproducing R0–R3/C0–C3 labels.
