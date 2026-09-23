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
single-analyst calibration review; it requires an independent blinded review
before publication.
