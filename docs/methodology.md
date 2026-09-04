# Methodology

## Study objective

The study asks what maintenance liabilities remain when an LLM successfully
implements a sequence of progressively refined requirements. It treats
functional correctness as an eligibility gate, not as evidence of structural
quality.

The unit of analysis is a `(trajectory, turn, condition, run)` checkpoint. A
trajectory is one SR-Eval Java repository task. A checkpoint is the complete
replacement method produced after a turn.

## Research questions

**RQ1 — Structural evolution.** How does reference-normalized structural
overhead change across progressive requirement refinements for functionally
correct LLM implementations?

**RQ2 — Reusability.** To what extent do LLM-generated evolutions miss
opportunities to reuse existing functionality and instead introduce redundant
implementations?

**RQ3 — Constraint adherence.** How reliably do LLMs follow explicit
software-engineering constraints across progressive requirement refinements?

**RQ4 — Evolutionary consequence.** Are structural overhead, missed reuse, or
constraint violations associated with increased effort or reduced success in
subsequent evolution steps?

## Experimental factors

| Factor | Pilot setting |
|---|---|
| Benchmark | SR-Eval Java repository-level subset |
| Context | Repository context on turn 1; prior generated method on later turns |
| Prompt strategy | SR-Eval code-edit strategy (`edit`) |
| Error propagation | Base/generated history, not golden history |
| Model | GPT-5.6 Sol |
| Reasoning | High |
| Automatic model routing | Disabled |
| Replications | 1 per trajectory/condition |
| Pilot A condition | Baseline instructions |
| Pilot B conditions | Baseline and fixed engineering guardrails |

The exact product/interface name, displayed model name, timestamps, permission
settings, and any observable tool configuration must be stored with every run.
A later full study should use multiple fixed model families and repeated runs;
the pilot is for methodology validation rather than population-level claims.

## Functional correctness

For checkpoint `t`, run tests `1..t` against the implementation generated at
turn `t`. A checkpoint is cumulatively correct only if all those tests pass.
This catches regressions that a current-turn-only test would miss.

All generated outputs are retained. The primary RQ1 and RQ2 analyses use
cumulatively correct checkpoints. Failure patterns remain available for RQ4 and
for reporting selection effects.

## Structural measurements

Measure both the LLM checkpoint and the corresponding SR-Eval reference
checkpoint using identical tooling and scope.

- logical lines of code and changed lines
- cyclomatic and cognitive complexity
- maximum nesting depth and branch count
- method-call count/fan-out
- helper-method creation
- code-smell count
- duplication candidates

For metric `m` at turn `t`, report absolute and normalized overhead:

```text
O(t,m)  = M(LLM,t,m) - M(REF,t,m)
NO(t,m) = (M(LLM,t,m) - M(REF,t,m)) / (M(REF,t,m) + epsilon)
```

Do not combine metrics into a single quality score during the pilot. Report
each dimension, its distribution, and missingness separately.

## Missed reuse

Automated duplication or semantic-similarity analysis generates candidates;
manual review determines whether reuse was reasonably available. Classify each
checkpoint:

- `R0`: no reuse opportunity
- `R1`: existing functionality reused
- `R2`: partially reused; some equivalent logic duplicated
- `R3`: available equivalent functionality was reimplemented

Reviewers must record the existing symbol or code region, the introduced
equivalent logic, and a concise rationale. For the full study, use independent
reviewers on a stratified subset and report inter-rater agreement.

## Guardrail adherence

Pilot B applies one identical guardrail block to six preselected trajectories.
Each resulting checkpoint is evaluated against five rules:

1. Inspect and reuse applicable existing behavior.
2. Preserve behavior introduced in preceding turns.
3. Avoid redundant helpers.
4. Avoid duplicate validation or transformation logic.
5. Avoid unrelated modifications.

Record each rule as `pass`, `fail`, or `not_applicable`, with evidence. Human
review is not an experimental treatment; the evidence may motivate continued
review without claiming a human-subject result.

## Downstream evolution effort

For turn `t+1`, record added/deleted lines, AST edit size when available,
replacement of existing implementation, functional regression, and repair
attempts. The pilot checks whether these variables have sufficient variation to
support RQ4; it does not fit a high-powered causal model.

## Reproducibility and exclusions

- Hash the exact prompt files and store their hashes in every run record.
- Pin the benchmark commit and retain its dataset hash.
- Use a fresh independent task session for every trajectory/condition.
- Do not manually repair a generation before recording its first-pass result.
- Do not discard failures or malformed responses.
- Replace a pilot task only for pre-generation executability failures and log
  the replacement before inspecting any model output for that task.
- Do not use employer artifacts or private production observations as data.
