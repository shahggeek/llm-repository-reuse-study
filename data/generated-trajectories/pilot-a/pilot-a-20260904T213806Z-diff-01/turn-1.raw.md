```java
public @NonNull ScoreAnalysis<Score_> diff(@NonNull ScoreAnalysis<Score_> other) {
    Objects.requireNonNull(other, "other");

    var constraintDiffMap = new HashMap<ConstraintRef, ConstraintAnalysis<Score_>>();
    Stream.concat(constraintMap.keySet().stream(), other.constraintMap().keySet().stream())
            .distinct()
            .forEach(constraintRef -> constraintDiffMap.put(
                    constraintRef,
                    Objects.requireNonNull(ConstraintAnalysis.diff(
                            constraintMap.get(constraintRef),
                            other.constraintMap().get(constraintRef)))));

    return new ScoreAnalysis<>(
            score.subtract(other.score()),
            constraintDiffMap,
            isSolutionInitialized && other.isSolutionInitialized());
}
```