# License scope

Copyright 2026 Gaurav V Shah.

The Apache License, Version 2.0 in `LICENSE` applies to the portions of this
repository authored for this study, including the Python and shell tooling,
tests, schemas, study-specific configuration, prompt templates, analysis code,
and original documentation.

It does **not** grant additional rights in:

- source-code excerpts, API signatures, copyright notices, or other material
  originating in third-party repositories;
- SR-Eval or MRG-Bench task instructions, decompositions, dataset rows, or
  prompt contexts;
- raw or extracted model outputs that may reproduce or adapt third-party code;
- test output copied from third-party build systems; or
- practitioner-authored ratings and rationales.

Those materials retain their existing rights and are described in
`THIRD_PARTY_LICENSES.md`. Their inclusion as research evidence does not imply
that the study author owns them or can relicense them.

Because the public SR-Eval and MRG-Bench repositories do not state a
redistribution license, this public artifact omits their authored task
instructions and rendered prompt text. Hashes bind the omitted text to the
private research record. A user who separately obtains SR-Eval at the pinned
revision may reconstruct and verify the prompts locally with:

```bash
python3 scripts/reconstruct_prompts.py \
  --sr-eval .cache/SR-Eval \
  --output reconstructed-prompts
```

The reconstructed files are local working material and are ignored by Git.
Nothing in this repository grants permission to redistribute them.
