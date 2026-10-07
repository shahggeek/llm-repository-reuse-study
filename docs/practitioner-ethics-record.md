# Practitioner-validation ethics record

Status: paper-facing disclosure prepared; venue guidance pending.

Record date: 2026-10-03

## Scope

The practitioner validation asked four experienced Java professionals to
compare six pairs of functionally correct implementations drawn from public
open-source repositories. The activity collected professional judgments about
repository fit, maintainability, approval readiness, duplicated behavior, and
future-change risk. It did not expose participants to employer code, internal
repositories, customer data, or confidential organizational information.

The validation was conducted by the author as independent research. It was not
conducted for, through, or on behalf of the author's employer. No formal
institutional ethics-board review or exemption determination was obtained
before recruitment. The author was not conducting the work through an
institution that provided an applicable ethics-review body for this research.
The paper must state this fact and must not describe the activity as IRB-
approved or IRB-exempt. A venue-guidance inquiry is prepared in
`docs/saner-industrial-ethics-inquiry-email.md`.

## Recruitment and participation

- Recruitment was purposive and based on professional Java and code-review
  experience.
- All four practitioners had substantial software-development experience
  specializing in Java.
- Four practitioners returned complete workbooks. The planned target was five,
  and the protocol's exploratory minimum was three.
- The supplied instructions estimated 45--60 minutes for the review.
- Participation was voluntary.
- Compensation was offered for participants' time. All four declined the
  compensation and completed the review voluntarily.
- The paper reports the sample as a convenience sample and makes no claim of
  representativeness.

## Information and consent

Before participating, every reviewer received the written instructions in
`outputs/industry-expert-review/industry-expert-review-instructions.md`. Those
instructions described:

- the purpose and procedure of the review;
- the expected time commitment;
- the requirement to use unaided human judgment;
- the data requested in the workbook;
- the intended aggregate or anonymous use of ratings, experience categories,
  and rationales in a research paper or artifact;
- the instruction not to provide employer, client, project, or proprietary
  information; and
- the option to stop before returning the workbook without giving a reason.

The Reviewer Profile sheet required an explicit Yes/No consent response. All
four included reviewers recorded Yes. The frozen intake record preserves that
fact, and the original returned workbooks remain unchanged.

## Data minimization and confidentiality

The research dataset contains:

- anonymous codes EXP-01 through EXP-04;
- broad experience and role categories;
- judgments and five-point ratings for the six supplied cases;
- short professional rationales;
- consent and AI-assistance declarations; and
- response dates and integrity hashes.

The workbook requested no participant name, email address, employer name,
repository name, company-specific detail, or proprietary code. Identity and
contact information used for correspondence is not part of the research
dataset or repository. Paper-facing analysis uses anonymous codes and aggregate
counts. Returned workbooks are excluded from the public Git repository; only
curated, anonymized derived data is eligible for release after a final privacy
review.

## Analysis and reporting protections

- The A/B treatment key remained concealed until the four completed responses
  and their hashes were frozen.
- Reviewers were instructed to use unaided human judgment and not to use AI;
  all four reported no AI assistance.
- The author converted the returned spreadsheet files into Apple Numbers
  working copies because Microsoft Excel was unavailable on the author's Mac.
  The original returns are retained separately in their received formats; the
  converted copies, not reviewer resubmissions, were used for local extraction.
- Results are descriptive because the reviewer and case samples are small and
  purposive.
- Two selected contrasts are checkpoints from one trajectory and are reported
  as dependent observations.
- The paper does not infer population prevalence, a general retrieval effect,
  or behavior in proprietary repositories.
- No employer or organization is named or implied as a study participant.

## Preserved evidence

- Participant instructions:
  `outputs/industry-expert-review/industry-expert-review-instructions.md`
- Study protocol:
  `analysis/rq2/industry-expert-validation-protocol.md`
- Frozen intake and response hashes:
  `results/pilot/industry-expert-review-intake-frozen.json`
- Anonymized analysis:
  `results/pilot/industry-expert-review-summary.json`
- Paper-facing findings:
  `analysis/rq2/industry-expert-validation-findings.md`

Private correspondence documenting the compensation offers and declines should
be retained by the author but must not be placed in the public artifact.

## Required paper disclosure

The manuscript must report that no formal institutional ethics-board review
was obtained, explain the independent-research context, describe written
consent and voluntary participation, disclose the declined compensation, and
summarize data minimization. Any later guidance from the SANER Industrial Track
chairs must be preserved and reflected accurately before submission.
