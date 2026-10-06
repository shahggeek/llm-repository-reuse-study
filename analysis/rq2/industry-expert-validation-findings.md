# Industry-expert validation findings

## Frozen response set

Recruitment closed on 2026-10-03 with four complete independent responses,
above the protocol minimum of three but below the target of five. All four
reviewers consented to anonymized research use, completed all six cases with
rationales, and reported no AI assistance after being instructed not to use
AI. All held bachelor's degrees in engineering and had professional Java and
large multi-module codebase experience. The author converted the returned
spreadsheet files into Numbers working copies for local extraction because
Excel was unavailable on the author's Mac; the original returns remain
separately preserved in their received formats. The working copies and their
SHA-256 hashes were frozen before the concealed A/B key was opened.

The 24 judgments are purposively selected descriptive evidence, not a random
sample. IE-RV-104 and IE-RV-105 are checkpoints from the same
`nodeArrayMerge` trajectory and are dependent.

## Planned reuse-sensitive contrasts

The planned contrasts are IE-RV-104, IE-RV-105, and IE-RV-106. Each reviewer
preferred the retrieval-supported implementation in all three cases (12/12
judgments). Every retrieval-supported implementation was approved (12/12),
whereas the comparator received three approvals and nine requests for changes.

All 12 paired repository-fit differences favored retrieval, with a median
difference of +2 on the five-point scale. All 12 maintainability differences
also favored retrieval, again with a median of +2. Reviewers assigned duplicated
repository behavior to the comparator in 10 judgments and to neither variant
in two. They assigned higher future-change risk to the comparator in nine,
retrieval in two, and were unsure in one. All 12 contrast judgments had high
confidence.

Rationales repeatedly favored delegating to repository-owned insertion or
growth helpers and avoiding duplicate policy that would require coordinated
future changes. These are concise descriptive themes, not a formal qualitative
coding study.

## Controls and disagreement

The controls show that reviewers did not mechanically favor the decoded
retrieval condition. Retrieval was preferred by 3/4 reviewers for IE-RV-101
and 4/4 for IE-RV-102, while the comparator was preferred by 3/4 for
IE-RV-103. Rationales for IE-RV-101 and IE-RV-103 sometimes prioritized the
literal local requirement or clearer direct behavior over use of a repository
helper. Each reviewer preferred retrieval in five of the six cases and the
comparator in one, but not always for the same control case.

## Interpretation boundary

The practitioner evidence supports the practical plausibility of the selected
reuse differences: experienced reviewers perceived better repository fit and
maintainability in the three preselected reuse-sensitive contrasts. It does
not estimate a general retrieval effect, establish performance in proprietary
repositories, or provide six independent replications. With four reviewers,
the protocol calls for unanimity and majority patterns rather than agreement
coefficients or population-level inference.
