```java
public ProductQuantization refine(RandomAccessVectorValues ravv,
                                  int lloydsRounds,
                                  float anisotropicThreshold,
                                  ForkJoinPool simdExecutor,
                                  ForkJoinPool parallelExecutor) {
    if (lloydsRounds < 0) {
        throw new IllegalArgumentException("lloydsRounds must be non-negative");
    }

    var subvectorSizesAndOffsets = getSubvectorSizesAndOffsets(ravv.dimension(), M);
    var vectors = extractTrainingVectors(ravv, parallelExecutor);

    if (globalCentroid != null) {
        var uncenteredVectors = vectors;
        vectors = simdExecutor.submit(() ->
                uncenteredVectors.parallelStream()
                        .map(v -> VectorUtil.sub(v, globalCentroid))
                        .collect(Collectors.<VectorFloat<?>>toList()))
                .join();
    }

    var trainingVectors = vectors;
    var refinedCodebooks = simdExecutor.submit(() ->
            IntStream.range(0, M)
                    .parallel()
                    .mapToObj(i -> {
                        int subvectorSize = subvectorSizesAndOffsets[i][0];
                        int subvectorOffset = subvectorSizesAndOffsets[i][1];

                        VectorFloat<?>[] subvectors = trainingVectors.stream()
                                .map(v -> v.copyFromTo(
                                        subvectorOffset,
                                        subvectorOffset + subvectorSize))
                                .toArray(VectorFloat<?>[]::new);

                        var clusterer = new KMeansPlusPlusClusterer(
                                subvectors, clusterCount, anisotropicThreshold);
                        return clusterer.cluster(lloydsRounds, codebooks[i]);
                    })
                    .toArray(VectorFloat<?>[]::new))
            .join();

    return new ProductQuantization(
            refinedCodebooks,
            clusterCount,
            subvectorSizesAndOffsets,
            globalCentroid,
            anisotropicThreshold);
}
```