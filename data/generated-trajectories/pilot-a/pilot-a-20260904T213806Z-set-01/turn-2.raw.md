```java
void set(Solution_ bestSolution, BooleanSupplier isEveryProblemChangeProcessed) {
    synchronized (this) {
        if (!isEveryProblemChangeProcessed.getAsBoolean()) {
            return;
        }
        this.versionedBestSolution =
                new VersionedBestSolution<>(bestSolution, this.currentVersion);
        this.currentVersion = this.currentVersion.add(BigInteger.ONE);
    }
}
```