```java
static KOptCycle getCyclesForPermutation(KOptDescriptor<?> kOptDescriptor) {
    int[] permutation = kOptDescriptor.removedEdgeIndexToTourOrder();
    boolean[] visited = new boolean[permutation.length];
    int[] indexToCycle = new int[permutation.length];
    int cycleCount = 0;

    for (int i = 0; i < permutation.length; i++) {
        if (visited[i]) {
            continue;
        }

        int current = i;
        while (!visited[current]) {
            visited[current] = true;
            indexToCycle[current] = cycleCount;
            current = permutation[current];
        }
        cycleCount++;
    }

    return new KOptCycle(cycleCount, indexToCycle);
}
```