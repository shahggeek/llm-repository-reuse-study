```java
static BuildScoreProvider randomAccessScoreProvider(
        RandomAccessVectorValues ravv,
        VectorSimilarityFunction similarityFunction) {
    ThreadLocal<RandomAccessVectorValues> threadLocalRavv =
            ThreadLocal.withInitial(ravv::copy);
    ThreadLocal<RandomAccessVectorValues> searchThreadLocalRavv =
            ThreadLocal.withInitial(ravv::copy);

    return new BuildScoreProvider() {
        @Override
        public boolean isExact() {
            return true;
        }

        @Override
        public VectorFloat<?> approximateCentroid() {
            RandomAccessVectorValues localRavv = threadLocalRavv.get();
            VectorFloat<?> centroid = vts.createFloatVector(localRavv.dimension());
            for (int i = 0; i < localRavv.size(); i++) {
                VectorUtil.addInPlace(centroid, localRavv.getVector(i));
            }
            VectorUtil.scale(centroid, 1.0f / localRavv.size());
            return centroid;
        }

        @Override
        public SearchScoreProvider searchProviderFor(VectorFloat<?> vector) {
            RandomAccessVectorValues localRavv = searchThreadLocalRavv.get();
            return SearchScoreProvider.exact(
                    vector, similarityFunction, localRavv);
        }

        @Override
        public SearchScoreProvider searchProviderFor(int node1) {
            RandomAccessVectorValues localRavv = threadLocalRavv.get();
            return SearchScoreProvider.exact(
                    localRavv.getVector(node1), similarityFunction, localRavv);
        }

        @Override
        public SearchScoreProvider diversityProviderFor(int node1) {
            return searchProviderFor(node1);
        }
    };
}
```