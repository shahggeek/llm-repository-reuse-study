# Industry expert validation protocol

## Objective

Test whether experienced software practitioners consider the observed reuse
differences practically meaningful in code review and future maintenance. This
is practical validation of the mechanism evidence, not another R0–R3 labeling
exercise and not an estimate of general LLM performance.

## Sample

- Target five completed reviewers; accept a minimum of three for exploratory
  reporting.
- Recruit practitioners with professional Java and code-review experience.
- Record only anonymous reviewer codes and broad experience categories.
- Do not collect employer names, repository names, emails, or proprietary code
  in the workbook.
- Before recruitment, confirm any ethics/IRB or organizational requirements
  that apply to the researchers. The workbook consent field does not replace an
  institution's required process.

## Materials and blinding

- Send each expert a fresh copy of
  `outputs/industry-expert-review/industry-expert-reuse-review.xlsx` and
  `outputs/industry-expert-review/industry-expert-review-instructions.md`.
- Assign codes `EXP-01`, `EXP-02`, and so on. Keep any identity-to-code mapping
  outside the research repository.
- Six A/B pairs are randomized and balanced. Experts receive the same
  repository context for both variants.
- Conceal condition names, run identifiers, R/C labels, study findings, and
  `results/pilot/industry-expert-review-blind-key.json` until all responses are
  frozen.
- Reviewers work independently and use no LLM or AI assistant.

## Selected cases

The purposive set includes two direct reuse contrasts, a later checkpoint from
the evolving `nodeArrayMerge` lineage, and three controls where both conditions
were already classified as appropriate reuse or no material reuse difference.
Every displayed implementation passed its cumulative functional checkpoint.

The controls are important: they allow packet presence and expert preference
to disagree, preventing the validation from becoming a set of only obvious
positive examples. Repeated `nodeArrayMerge` checkpoints remain dependent and
must not be presented as independent replications.

## Administration

1. Send the identical blank package to every expert.
2. Do not explain which cases are expected to differ.
3. Answer procedural questions only. If a material clarification is necessary,
   send the same written clarification to every active reviewer and record it.
4. On return, preserve the original workbook unchanged and record its SHA-256.
5. Extract responses to a separate table; never overwrite returned files.
6. Reveal the blind key only after all planned reviewers have submitted or the
   recruitment window is formally closed.

## Primary inclusion rules

A workbook enters the primary analysis when:

- consent is Yes;
- the reviewer confirms no AI/LLM assistance;
- all six case rows have a preferred implementation, both approval decisions,
  both repository-fit scores, both maintainability scores, duplication and
  future-risk judgments, confidence, and a rationale; and
- case IDs and workbook structure are unchanged.

Incomplete responses may be summarized as attrition. AI-assisted responses may
be retained only for a clearly separated sensitivity analysis.

## Analysis plan

Report descriptive results because the expert sample and case set are small and
purposive:

- preferred implementation counts per case and overall;
- A/B approval-decision distributions;
- paired within-reviewer differences in repository-fit and maintainability
  scores;
- counts for duplicated behavior and higher future-change risk;
- confidence distribution; and
- concise qualitative themes from rationales, with anonymous quotations when
  consent permits.

Decode A/B only after response freezing. Present results by treatment and by
trajectory lineage. Do not treat the two `nodeArrayMerge` checkpoints as
independent cases in inferential claims. With at least three complete reviewers,
report unanimity/majority patterns. With five, add agreement statistics where
the category distribution makes them interpretable, but do not make
population-level significance claims.

## Reporting boundary

The expert review can support claims that practitioners perceive a concrete
repository-fit or maintenance difference in these open-source cases. It cannot
establish a general retrieval effect, replace cross-repository replication, or
show how proprietary industrial repositories behave.
