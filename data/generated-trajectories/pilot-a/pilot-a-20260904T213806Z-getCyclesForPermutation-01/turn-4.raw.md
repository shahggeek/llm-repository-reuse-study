```java
static KOptCycle getCyclesForPermutation(KOptDescriptor<?> kOptDescriptor) {
    int[] removedEdgeIndexToTourOrder =
            kOptDescriptor.removedEdgeIndexToTourOrder();
    int[] addedEdgeToOtherEndpoint =
            kOptDescriptor.addedEdgeToOtherEndpoint();
    int[] inverseRemovedEdgeIndexToTourOrder =
            kOptDescriptor.inverseRemovedEdgeIndexToTourOrder();

    int[] indexToCycle = new int[removedEdgeIndexToTourOrder.length];
    BitSet unvisited = new BitSet(removedEdgeIndexToTourOrder.length);
    unvisited.set(1, removedEdgeIndexToTourOrder.length);

    int cycleCount = 0;
    while (!unvisited.isEmpty()) {
        int startEndpoint = unvisited.nextSetBit(1);
        int currentEndpoint = startEndpoint;

        do {
            unvisited.clear(currentEndpoint);
            indexToCycle[currentEndpoint] = cycleCount;

            int tourOrder = removedEdgeIndexToTourOrder[currentEndpoint];
            int addedEdgeEndpoint = addedEdgeToOtherEndpoint[tourOrder];
            currentEndpoint =
                    inverseRemovedEdgeIndexToTourOrder[addedEdgeEndpoint];
        } while (currentEndpoint != startEndpoint);

        cycleCount++;
    }

    return new KOptCycle(cycleCount, indexToCycle);
}
```