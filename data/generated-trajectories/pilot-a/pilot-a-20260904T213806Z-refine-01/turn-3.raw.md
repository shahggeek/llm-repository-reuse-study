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
        var originalVectors = vectors;
        vectors = simdExecutor.submit(() ->
                originalVectors.parallelStream()
                        .map(vector -> VectorUtil.sub(vector, globalCentroid))
                        .collect(Collectors.<VectorFloat<?>>toList()))
                .join();
    }

    var centeredVectors = vectors;
    var refinedCodebooks = simdExecutor.submit(() ->
            IntStream.range(0, M)
                    .parallel()
                    .mapToObj(m -> {
                        var subvectors = extractSubvectors(
                                centeredVectors, m, subvectorSizesAndOffsets);
                        var clusterer = new KMeansPlusPlusClusterer(
                                subvectors, clusterCount, anisotropicThreshold);
                        return clusterer.cluster(lloydsRounds, codebooks[m]);
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