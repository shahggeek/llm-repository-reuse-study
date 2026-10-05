```java
public @NonNull ScoreAnalysis<Score_> diff(@NonNull ScoreAnalysis<Score_> other) {
    Objects.requireNonNull(other, "other");

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
        constraintAnalysisDiffMap.put(constraintRef, constraintAnalysisDiff);
    }

    return new ScoreAnalysis<>(
            score.subtract(other.score),
            constraintAnalysisDiffMap,
            isSolutionInitialized && other.isSolutionInitialized);
}
```