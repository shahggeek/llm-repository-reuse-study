# Pilot A Reuse Review Rubric

Status: pilot operationalization. This extends the frozen R0–R3 definitions in
`docs/methodology.md`; it does not change the underlying research question.

## Unit and evidence

The unit is one functionally correct generated/reference checkpoint pair. The
reference implementation is a candidate locator, not an architectural oracle.
A call difference alone is never sufficient evidence of missed reuse.

For every reviewed checkpoint, record:

1. the existing repository symbol or code region;
2. the generated code that reuses, partially duplicates, or replaces it;
3. whether the candidate was available in the supplied model context;
4. the likely maintenance consequence; and
5. uncertainty or a plausible justification for the generated alternative.

## Reuse classification

- **R0 — no credible reuse opportunity.** No existing repository abstraction
  materially covers the requested behavior.
- **R1 — appropriate reuse.** The generated implementation uses the relevant
  abstraction, or uses a comparably suitable library abstraction without
  creating meaningful duplication.
- **R2 — partial reuse with duplicated behavior.** The implementation reuses
  some relevant facilities but reproduces a meaningful part of behavior owned
  by an existing abstraction.
- **R3 — reimplementation of available functionality.** A compatible existing
  repository abstraction covers the behavior, but the generated method
  independently reimplements it.

R2 and R3 identify repository-level missed reuse. They do not by themselves
attribute fault to the model; use the context classification below for that.

## Context availability

- **C0 — not applicable.** No concrete reuse candidate exists.
- **C1 — repository-only/latent.** The abstraction exists in the repository or
  reference solution but its name or implementation was not present in the
  supplied prompt context.
- **C2 — discoverable cue.** The supplied context contains a type, import,
  neighboring use, or convention that points toward the abstraction, but does
  not explicitly name the applicable method.
- **C3 — explicit.** The instruction or supplied context explicitly names or
  shows the applicable method.

Only an R2/R3 event paired with C2 or C3 supports a claim that the model missed
reuse despite usable context. R2/R3 with C1 instead supports a context-coverage
or retrieval hypothesis.

## Decision rules

- Treat alternative standard-library calls as R1 when they preserve the same
  policy and do not create a second repository-owned implementation.
- Do not penalize a generated checkpoint for omitting behavior introduced only
  in a later turn, even if the same-turn reference includes it.
- Do not infer missed reuse from shorter or longer code alone.
- Record the highest class supported by concrete evidence; choose the lower
  class when helper suitability or semantic equivalence is uncertain.
- Review repeated checkpoints within one trajectory as dependent observations.
  Report both checkpoint and trajectory counts.

## Reliability procedure

The current pilot is a single-analyst, non-blinded calibration review. Before
publication, a second reviewer should independently classify a stratified
sample with generated/reference origin labels masked, then resolve
disagreements and report raw agreement and weighted Cohen's kappa. Until that
happens, the manual classifications are feasibility evidence, not final study
measurements.
