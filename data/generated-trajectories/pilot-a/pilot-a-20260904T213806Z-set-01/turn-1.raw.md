```java
void set(Solution_ bestSolution) {
    synchronized (this) {
        this.versionedBestSolution =
                new VersionedBestSolution<>(bestSolution, this.currentVersion);
        this.currentVersion = this.currentVersion.add(BigInteger.ONE);
    }
}
```