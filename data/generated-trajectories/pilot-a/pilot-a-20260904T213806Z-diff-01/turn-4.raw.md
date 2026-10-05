```java
public @NonNull ScoreAnalysis<Score_> diff(@NonNull ScoreAnalysis<Score_> other) {
    Objects.requireNonNull(other, "other");

    boolean hasMatchData = constraintMap.values().stream()
            .anyMatch(constraintAnalysis -> constraintAnalysis.matches() != null);
    boolean otherHasMatchData = other.constraintMap().values().stream()
            .anyMatch(constraintAnalysis -> constraintAnalysis.matches() != null);
    if (hasMatchData != otherHasMatchData) {
        throw new IllegalArgumentException(
                "Cannot diff score analyses with incompatible match-data availability.");
    }

    var constraintDiffMap = new HashMap<ConstraintRef, ConstraintAnalysis<Score_>>();
    Stream.concat(constraintMap.keySet().stream(), other.constraintMap().keySet().stream())
            .distinct()
            .forEach(constraintRef -> {
                var constraintDiff = ConstraintAnalysis.diff(
                        constraintMap.get(constraintRef),
                        other.constraintMap().get(constraintRef));
                if (constraintDiff != null) {
                    constraintDiffMap.put(constraintRef, constraintDiff);
                }
            });

    return new ScoreAnalysis<>(
            score.subtract(other.score()),
            constraintDiffMap,
            isSolutionInitialized);
}
```