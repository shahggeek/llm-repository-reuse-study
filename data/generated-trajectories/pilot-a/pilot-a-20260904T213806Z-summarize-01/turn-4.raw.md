```java
public @NonNull String summarize() {
    var summary = new StringBuilder("Explanation of score (")
            .append(score)
            .append("):\n");

    constraintAnalyses().stream()
            .sorted(comparing(ConstraintAnalysis<Score_>::score))
            .forEach(constraintAnalysis -> {
                var matches = constraintAnalysis.matches();
                if (matches == null) {
                    throw new IllegalArgumentException(
                            "Constraint matches are unavailable. Use ScoreAnalysisFetchPolicy.FETCH_ALL to include them.");
                }

                summary.append("    ")
                        .append(constraintAnalysis.constraintRef().constraintName())
                        .append(": ")
                        .append(constraintAnalysis.score())
                        .append(" (")
                        .append(constraintAnalysis.matchCount())
                        .append(" matches)")
                        .append('\n');

                if (matches.isEmpty()) {
                    summary.append("        No matches.\n");
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

                if (matches.size() > DEFAULT_SUMMARY_CONSTRAINT_MATCH_LIMIT) {
                    summary.append("        ...\n");
                }
            });

    return summary.toString();
}
```