```java
static BuildScoreProvider randomAccessScoreProvider(RandomAccessVectorValues ravv, VectorSimilarityFunction similarityFunction) {
    var threadLocalRavv = ThreadLocal.withInitial(ravv::copy);
    var searchThreadLocalRavv = ThreadLocal.withInitial(ravv::copy);
    var diversityThreadLocalRavv = ThreadLocal.withInitial(ravv::copy);

    return new BuildScoreProvider() {
        @Override
        public boolean isExact() {
            return true;
        }

        @Override
        public VectorFloat<?> approximateCentroid() {
            var localRavv = threadLocalRavv.get();
            var centroid = vts.createFloatVector(localRavv.dimension());
            for (int i = 0; i < localRavv.size(); i++) {
                VectorUtil.addInPlace(centroid, localRavv.vectorValue(i));
            }
            VectorUtil.scale(centroid, 1.0f / localRavv.size());
            return centroid;
        }

        @Override
        public SearchScoreProvider searchProviderFor(VectorFloat<?> vector) {
            return SearchScoreProvider.exact(vector, similarityFunction, searchThreadLocalRavv.get());
        }

        @Override
        public SearchScoreProvider searchProviderFor(int node1) {
            return searchProviderFor(threadLocalRavv.get().vectorValue(node1));
        }

        @Override
        public SearchScoreProvider diversityProviderFor(int node1) {
            return SearchScoreProvider.exact(
                    threadLocalRavv.get().vectorValue(node1),
                    similarityFunction,
                    diversityThreadLocalRavv.get());
        }
    };
}
```