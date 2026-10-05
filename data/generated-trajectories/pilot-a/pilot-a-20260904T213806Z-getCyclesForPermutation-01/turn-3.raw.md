```java
static KOptCycle getCyclesForPermutation(KOptDescriptor<?> kOptDescriptor) {
    int[] addedEdgeToOtherEndpoint =
            kOptDescriptor.addedEdgeToOtherEndpoint();

    int[] indexToCycle = new int[addedEdgeToOtherEndpoint.length];
    BitSet unvisited = new BitSet(addedEdgeToOtherEndpoint.length);
    unvisited.set(0, addedEdgeToOtherEndpoint.length);

    int cycleCount = 0;
    while (!unvisited.isEmpty()) {
        int startEndpoint = unvisited.nextSetBit(0);
        int currentEndpoint = startEndpoint;

        do {
            unvisited.clear(currentEndpoint);
            indexToCycle[currentEndpoint] = cycleCount;

            currentEndpoint = addedEdgeToOtherEndpoint[currentEndpoint];
            unvisited.clear(currentEndpoint);
            indexToCycle[currentEndpoint] = cycleCount;

            currentEndpoint = currentEndpoint ^ 1;
        } while (currentEndpoint != startEndpoint);

        cycleCount++;
    }

    return new KOptCycle(cycleCount, indexToCycle);
}
```