# RQ2 — Reusability

Current artifacts:

- `reuse-rubric.md`: operational R0–R3 and C0–C3 review rules.
- `industry-expert-validation-protocol.md`: blinded practical-validation
  protocol for human code-review and maintenance judgments.
- `pilot-reuse-findings.md`: complete Pilot A reuse findings and NARROW
  decision.
- `blinded-review-protocol.md`: independent review and agreement procedure.
- `../../outputs/pilot-a-reuse-independent-review/pilot-a-reuse-blinded-review.xlsx`:
  blinded A/B reviewer workbook.
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
