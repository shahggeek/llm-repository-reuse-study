# Pilot Task Selection

The authoritative selection is `experiment/config/pilot-tasks.json`. Tasks are
identified by SR-Eval hash rather than function name because the dataset contains
ambiguous names such as `merge`, `summarize`, and
`calculatePhaseTimeGradient`.

The sample deliberately combines 12 structurally rich trajectories with 6
smaller controls. It is a purposive methodology pilot, not a random or
representative sample of all SR-Eval tasks.

Use `python3 scripts/pilot.py validate --sr-eval <path>` to confirm that every
hash, repository, function name, and turn count matches the pinned dataset.
Use the `export` command to create local task packets under `work/task-packets`;
those packets include benchmark reference code/tests and should not be edited or
treated as generated outcomes.
