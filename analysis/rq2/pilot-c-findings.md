# Pilot C cross-repository findings

Pilot C completed all 12 frozen trajectories (24 checkpoints). The cumulative
functional gate passed 18 of 36
test executions; 12 of 24
checkpoints were eligible for primary reuse analysis.

| Repository/task | Guardrails correct | Retrieval correct | Interpretation |
|---|---:|---:|---|
| LangChain4j `loadDocumentsRecursively` | 6/6 | 6/6 | All 12 checkpoints reused the repository stream helper (R1); ceiling in both conditions. |
| Spring AI `merge` | 0/6 | 0/6 | Ineligible: compilation, repository-style, or exact behavioral-contract failures. |

For Spring AI, the retrieval packet changed repository-API uptake even though
it did not restore correctness: all four supplied symbols appeared in
6/6 retrieval checkpoints versus
1/6 guardrails-only checkpoints. This is diagnostic evidence, not a primary reuse
result, because none of those checkpoints passed the functional gate.

The defensible conclusion is narrow: making repository APIs explicit can make
the model use them, but API visibility alone does not guarantee repository-fit
correctness. This replication does not establish a broad cross-repository
causal effect; one task is a reuse ceiling and the other has zero eligible
checkpoints.
