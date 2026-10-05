```java
static KOptCycle getCyclesForPermutation(KOptDescriptor<?> kOptDescriptor) {
    int[] removedEdgeIndexToTourOrder =
            kOptDescriptor.removedEdgeIndexToTourOrder();
    int[] inverseRemovedEdgeIndexToTourOrder =
            kOptDescriptor.inverseRemovedEdgeIndexToTourOrder();
    int[] addedEdgeToOtherEndpoint =
            kOptDescriptor.addedEdgeToOtherEndpoint();

    int[] indexToCycle = new int[addedEdgeToOtherEndpoint.length];
    BitSet unvisited = new BitSet(addedEdgeToOtherEndpoint.length);
    unvisited.set(1, addedEdgeToOtherEndpoint.length);

    int cycleCount = 0;
    while (!unvisited.isEmpty()) {
        int start = unvisited.nextSetBit(1);
        int current = start;

        do {
            unvisited.clear(current);
            indexToCycle[current] = cycleCount;

            int tourOrder = removedEdgeIndexToTourOrder[current];
            int adjacentTourOrder = (tourOrder & 1) == 0
                    ? tourOrder - 1
                    : tourOrder + 1;
            int adjacentEndpoint =
                    inverseRemovedEdgeIndexToTourOrder[adjacentTourOrder];

            unvisited.clear(adjacentEndpoint);
            indexToCycle[adjacentEndpoint] = cycleCount;

            current = addedEdgeToOtherEndpoint[adjacentEndpoint];
        } while (current != start);

        cycleCount++;
    }

    return new KOptCycle(cycleCount, indexToCycle);
}
```