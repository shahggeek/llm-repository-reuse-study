# Third-party material and attribution

This file records the origin and known licensing status of third-party
material relevant to the public evidence package. It is informational and does
not replace the license text supplied by any upstream copyright holder.

## Benchmark sources not redistributed

| Project | Source | Licensing status checked 2026-10-05 | Public-artifact treatment |
|---|---|---|---|
| SR-Eval | <https://github.com/AjaxZhan/SR-Eval> | No repository license identified | Benchmark-authored instructions and rendered prompts are omitted. Users obtain the pinned checkout separately for local reconstruction. |
| MRG-Bench | <https://github.com/MRG-Bench/MRG-Bench> | No repository license identified | Dataset-authored instructions and records are not redistributed independently; SR-Eval identifies MRG-Bench as their source. |

The study pins SR-Eval commit
`6cf948d69427687bf61042640223d5b318f7bc4c`. Public run records retain SHA-256
digests of omitted instructions and prompts. `scripts/reconstruct_prompts.py`
verifies locally reconstructed text against those digests.

## Upstream repositories represented in the evidence

The selected Java tasks originate in the following projects. Their repository
code is licensed under the Apache License, Version 2.0. Copyright and license
headers present in included excerpts must be retained.

| Project | Source | License |
|---|---|---|
| JVector | <https://github.com/datastax/jvector> | Apache-2.0 |
| Spring AI | <https://github.com/spring-projects/spring-ai> | Apache-2.0 |
| Timefold Solver | <https://github.com/TimefoldAI/timefold-solver> | Apache-2.0 |
| LangChain4j | <https://github.com/langchain4j/langchain4j> | Apache-2.0 |
| MyBatis-Flex | <https://github.com/mybatis-flex/mybatis-flex> | Apache-2.0 |

The complete Apache License, Version 2.0 is included in `LICENSE`. The
top-level license applies to study-authored material as defined in
`LICENSE_SCOPE.md`; third-party copyrights remain with their owners.

## Model and practitioner evidence

Raw and extracted model outputs are preserved as experimental observations.
They are not represented as exclusively owned by the study author and are not
relicensed by the top-level Apache license.

Anonymous practitioner ratings and rationales are released only as the
deidentified research evidence described by the study's ethics record. The
top-level Apache license does not grant additional rights in a participant's
authored rationale.
