# Structural metric definitions

The Pilot A extractor uses Tree-sitter 0.25.2 with the Java grammar 0.23.5.
Each generated method and its same-turn SR-Eval reference method are parsed as
the sole member of a synthetic wrapper class. A pair is rejected rather than
partially measured when either method has a parse error.

Lizard 1.17.31 independently recalculates cyclomatic complexity for every
method. The pipeline fails on any discrepancy; the completed 48-method run had
zero discrepancies.

## Selection

The primary structural dataset contains the 24 checkpoints that are both
cumulatively correct and eligible under the frozen reference/prompt-conflict
rules. The strict context-sufficiency subgroup contains 16 of those checkpoints
whose exact integration-critical signature was supplied literally. The
post-generation exclusion of `rerank` does not change either structural set
because no `rerank` checkpoint compiled.

## Metrics

- `physical_lines`: lines in the method snippet, including braces and comments.
- `source_lines_nonblank_noncomment`: non-empty lines after lexical removal of
  Java line and block comments; comment markers inside strings/chars are kept.
- `statement_count`: Tree-sitter statement and local-variable nodes.
- `cyclomatic_complexity`: 1 plus `if`, loop, `catch`, ternary, non-default
  switch-case, and boolean `&&`/`||` decision nodes.
- `cognitive_complexity_approx`: deterministic nesting-weighted decision count.
  This is a study-specific approximation and must not be described as
  SonarQube's implementation.
- `max_control_nesting`: deepest nesting of conditionals, loops, switches,
  catches, synchronized blocks, ternaries, and lambdas.
- `branch_count`: conditionals, loops, catches, ternaries, and non-default
  switch cases, excluding boolean subexpressions.
- `method_invocation_count` and `constructor_invocation_count`: Tree-sitter
  invocation nodes.
- `unique_call_target_count`: distinct invoked method names and constructed
  type names; it is a lexical fan-out proxy, not resolved call-graph fan-out.
- Parameter, return, throw, local-variable, and lambda counts come directly
  from their AST nodes.
- `code_smell_count`: count of four transparent screening flags: more than 40
  source lines, cyclomatic complexity above 10, control nesting above 3, and
  more than four parameters. It is not a composite quality score.

For each metric `m`, the extractor records absolute and normalized overhead:

```text
absolute = generated(m) - reference(m)
normalized = absolute / (reference(m) + 1e-9)
```

Rows flag zero-valued references. Aggregate normalized summaries omit those
rows because epsilon-scaled values are not substantively interpretable.

## Interpretation limits

Checkpoints from the same trajectory are dependent observations. Pilot tables
are descriptive and should emphasize paired medians, signs, task-level
patterns, and the strict subgroup. The top-level paired mean and median
overheads include deterministic 95% percentile intervals from 5,000 bootstrap
resamples clustered by trajectory. These intervals describe pilot uncertainty;
they are not population-level model-performance estimates. Duplicate/reuse
detection belongs to RQ2 and is not inferred from call counts alone.
