# Prompt-Context Sufficiency Audit

Date: 2026-09-23  
Scope: all 18 tasks in the adjusted Pilot A sample  
Timing: post-generation

## Purpose

This audit checks whether each model prompt contained enough information to
produce a Java method that could integrate with the pinned repository. It does
not judge algorithmic correctness. The audit focuses on the method name,
return type, parameter count/order/types, checked exceptions, and any
repository-specific container or callback types required by existing callers.

Because the audit was initiated after model outcomes were known, it cannot be
used to silently redefine the frozen primary result. Its classifications are
used for transparent sensitivity analyses. Raw generations and test results
remain unchanged.

## Rubric

- **Explicit-consistent:** the integration-critical signature is supplied
  literally and agrees with the reference/repository contract.
- **Inferable-consistent:** a literal signature is absent, but the instruction
  and supplied class/import context identify the return behavior and typed
  parameters without requiring a hidden repository-specific type.
- **Partially-conflicting:** at least one checkpoint supplies a signature that
  conflicts with the reference or an existing caller.
- **Underspecified integration types:** compilation requires repository-specific
  types that are absent from both the instruction and supplied context.

## Task-by-task result

| Task | Classification | Audit result |
|---|---|---|
| `invert` | Inferable-consistent | Matrix class, no arguments, and Matrix return behavior are supplied. |
| `nodeArrayMerge` | Explicit-consistent | Complete `NodeArray` signature supplied. |
| `refine` | Explicit-consistent | Complete generic return and five typed parameters supplied. |
| `encodeAnisotropic` | Explicit-consistent | Complete private method signature supplied. |
| `removeDeletedNodes` | Explicit-consistent | Complete base signature supplied; later synchronization does not change caller types. |
| `writeInline` | Inferable-consistent | Typed parameters are named; I/O imports and synchronized I/O methods appear in context. |
| `randomAccessScoreProvider` | Explicit-consistent | Complete return and parameter types supplied. |
| `calculatePhaseTimeGradient` | Inferable-consistent | Double result and full generic parameter type supplied; type is imported in context. |
| `getCyclesForPermutation` | Explicit-consistent | Complete static generic signature supplied. |
| `diff` | Explicit-consistent | Complete annotated generic signature supplied. |
| `summarize` | Explicit-consistent | Integration-critical signature supplied; later warning annotation is non-semantic. |
| `ensureCapacity` | Explicit-consistent | Complete static signature supplied. |
| `methodToProperty` | Explicit-consistent | Complete static signature supplied. |
| `set` | Partially-conflicting | Turn 1 omits the caller-required `BooleanSupplier`; turns 2–3 correct it. |
| `underlineToCamel` | Explicit-consistent | Complete static signature supplied. |
| `loadDocuments` | Explicit-consistent | Complete generic return and parameter types supplied. |
| `rerank` | Underspecified integration types | `ExactScoreFunction`, `NodesUnsorted`, and the caller contract are absent from the supplied material. |
| `addInOrder` | Explicit-consistent | Complete method signature supplied. |

Totals: 13 explicit-consistent, three inferable-consistent, one partially
conflicting, and one underspecified.

## Sensitivity results

The frozen primary result remains the main preregistered-style view. Two
post-generation sensitivity views quantify the context risk:

| View | Eligible tasks | Eligible checkpoints | Correct checkpoints | Correctness yield |
|---|---:|---:|---:|---:|
| Frozen primary exclusions | 18 | 61 | 24 | 39.3% |
| Exclude only clearly underspecified `rerank` | 17 | 57 | 24 | 42.1% |
| Strict: literal signatures only | 14 | 44 | 16 | 36.4% |

The central conclusion is stable: a usable but selective pool of correct
checkpoints remains, and correctness degrades across progressive turns. The
24-checkpoint structural/reuse pool is unchanged by excluding `rerank`, because
none of its checkpoints compiled. The strict view removes eight correct
checkpoints from `invert` and `calculatePhaseTimeGradient`; it is deliberately
conservative and should be reported as a robustness bound rather than a new
primary estimate.

## Data-quality decision

1. Preserve all original outputs and the frozen primary result.
2. Report the clear-case and strict sensitivity views alongside it.
3. Exclude `rerank` from claims that attribute its compilation failures solely
   to model capability; classify it as context/repository-integration
   ambiguity.
4. Continue to exclude `set` turn 1 under the already frozen conflict rule.
5. For Pilot B and any full study, require a literal, repository-compatible
   method signature in every turn-1 prompt before model generation.
6. Have a second human reviewer confirm the three inferable classifications
   before submitting the paper.

The machine-readable evidence and decisions are stored in
`results/pilot/prompt-context-sufficiency-audit.json` and validated by
`scripts/audit_prompt_context.py`.
