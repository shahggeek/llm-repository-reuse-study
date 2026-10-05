```java
public @NonNull String summarize() {
    var summary = new StringBuilder("Score analysis: ")
            .append(score)
            .append('\n');

    constraintAnalyses().stream()
            .sorted(comparing(ConstraintAnalysis<Score_>::score))
            .forEach(constraintAnalysis -> {
                summary.append("    ")
                        .append(constraintAnalysis.constraintRef().constraintName())
                        .append(": ")
                        .append(constraintAnalysis.score())
                        .append(" (")
                        .append(constraintAnalysis.matchCount())
                        .append(" matches)")
                        .append('\n');

                var matches = constraintAnalysis.matches();
                if (matches == null || matches.isEmpty()) {
                    if (constraintAnalysis.matchCount() == 0) {
                        summary.append("        No matches.\n");
                    }
                    return;
                }

                matches.stream()
                        .sorted(comparing(MatchAnalysis<Score_>::score))
                        .limit(DEFAULT_SUMMARY_CONSTRAINT_MATCH_LIMIT)
                        .forEach(matchAnalysis -> summary.append("        ")
                                .append(matchAnalysis.score())
                                .append(": ")
                                .append(matchAnalysis.justification())
                                .append('\n'));
            });

    return summary.toString();
}
```