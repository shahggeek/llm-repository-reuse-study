```java
public @NonNull ScoreAnalysis<Score_> diff(@NonNull ScoreAnalysis<Score_> other) {
    Objects.requireNonNull(other, "other");

    var hasMatchData = constraintMap.values().stream()
            .anyMatch(constraintAnalysis -> constraintAnalysis.matches() != null);
    var otherHasMatchData = other.constraintMap.values().stream()
            .anyMatch(constraintAnalysis -> constraintAnalysis.matches() != null);
    if (hasMatchData != otherHasMatchData) {
        throw new IllegalArgumentException("Cannot diff score analyses with incompatible match data.");
    }

    var constraintAnalysisDiffMap = new HashMap<ConstraintRef, ConstraintAnalysis<Score_>>();
    var constraintRefs = Stream.concat(constraintMap.keySet().stream(), other.constraintMap.keySet().stream())
            .distinct()
            .toList();

    for (var constraintRef : constraintRefs) {
        var constraintAnalysis = constraintMap.get(constraintRef);
        var otherConstraintAnalysis = other.constraintMap.get(constraintRef);

        ConstraintAnalysis<Score_> constraintAnalysisDiff;
        if (constraintAnalysis == null) {
            constraintAnalysisDiff = Objects.requireNonNull(otherConstraintAnalysis).negate();
        } else if (otherConstraintAnalysis == null) {
            constraintAnalysisDiff = constraintAnalysis;
        } else {
            constraintAnalysisDiff = constraintAnalysis.diff(otherConstraintAnalysis);
        }

        var matchAnalysisDiffs = constraintAnalysisDiff.matches();
        if (!constraintAnalysisDiff.weight().isZero()
                || !constraintAnalysisDiff.score().isZero()
                || (matchAnalysisDiffs != null && !matchAnalysisDiffs.isEmpty())) {
            constraintAnalysisDiffMap.put(constraintRef, constraintAnalysisDiff);
        }
    }

    return new ScoreAnalysis<>(
            score.subtract(other.score),
            constraintAnalysisDiffMap,
            isSolutionInitialized);
}
```