```java
static BuildScoreProvider randomAccessScoreProvider(RandomAccessVectorValues ravv, VectorSimilarityFunction similarityFunction) {
    var ravvSupplier = ravv.threadLocalSupplier();
    var queryRavvSupplier = ravv.threadLocalSupplier();

    return new BuildScoreProvider() {
        @Override
        public boolean isExact() {
            return true;
        }

        @Override
        public VectorFloat<?> approximateCentroid() {
            var localRavv = ravvSupplier.get();
            var centroid = vts.createFloatVector(localRavv.dimension());

            for (int i = 0; i < localRavv.size(); i++) {
                VectorUtil.addInPlace(centroid, localRavv.vectorValue(i));
            }

            VectorUtil.scale(centroid, 1.0f / localRavv.size());
            return centroid;
        }

        @Override
        public SearchScoreProvider searchProviderFor(VectorFloat<?> vector) {
            var localRavv = ravvSupplier.get();
            return SearchScoreProvider.exact(vector, similarityFunction, localRavv);
        }

        @Override
        public SearchScoreProvider searchProviderFor(int node1) {
            var queryRavv = queryRavvSupplier.get();
            return searchProviderFor(queryRavv.vectorValue(node1));
        }

        @Override
        public SearchScoreProvider diversityProviderFor(int node1) {
            return searchProviderFor(node1);
        }
    };
}
```