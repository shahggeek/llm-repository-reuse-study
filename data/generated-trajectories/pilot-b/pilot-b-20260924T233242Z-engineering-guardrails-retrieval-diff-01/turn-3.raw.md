```java
public @NonNull ScoreAnalysis<Score_> diff(@NonNull ScoreAnalysis<Score_> other) {
    Objects.requireNonNull(other, "other");

    var constraintRefSet = Stream.of(constraintMap.keySet(), other.constraintMap.keySet())
            .flatMap(Collection::stream)
            .collect(Collectors.toSet());
    Map<ConstraintRef, ConstraintAnalysis<Score_>> constraintDiffMap =
            new HashMap<>(constraintRefSet.size());

    for (var constraintRef : constraintRefSet) {
        var constraintDiff = ConstraintAnalysis.diff(
                constraintRef,
                getConstraintAnalysis(constraintRef),
                other.getConstraintAnalysis(constraintRef));
        var matchDiffs = constraintDiff.matches();

        if (!constraintDiff.weight().equals(constraintDiff.weight().zero())
                || !constraintDiff.score().equals(constraintDiff.score().zero())
                || (matchDiffs != null && !matchDiffs.isEmpty())) {
            constraintDiffMap.put(constraintRef, constraintDiff);
        }
    }

    return new ScoreAnalysis<>(
            score.subtract(other.score),
            constraintDiffMap,
            isSolutionInitialized && other.isSolutionInitialized);
}
```