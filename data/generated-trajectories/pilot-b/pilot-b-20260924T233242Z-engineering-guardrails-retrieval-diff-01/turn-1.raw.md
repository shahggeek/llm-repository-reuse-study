```java
public @NonNull ScoreAnalysis<Score_> diff(@NonNull ScoreAnalysis<Score_> other) {
    Objects.requireNonNull(other, "other");

    var constraintRefSet = Stream.of(constraintMap.keySet(), other.constraintMap.keySet())
            .flatMap(Collection::stream)
            .collect(Collectors.toSet());
    Map<ConstraintRef, ConstraintAnalysis<Score_>> constraintDiffMap =
            new HashMap<>(constraintRefSet.size());

    for (var constraintRef : constraintRefSet) {
        constraintDiffMap.put(constraintRef,
                ConstraintAnalysis.diff(constraintRef,
                        getConstraintAnalysis(constraintRef),
                        other.getConstraintAnalysis(constraintRef)));
    }

    return new ScoreAnalysis<>(
            score.subtract(other.score),
            constraintDiffMap,
            isSolutionInitialized && other.isSolutionInitialized);
}
```