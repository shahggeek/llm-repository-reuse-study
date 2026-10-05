```java
static BuildScoreProvider randomAccessScoreProvider(RandomAccessVectorValues ravv, VectorSimilarityFunction similarityFunction) {
    var ravvSupplier = ravv.threadLocalSupplier();

    return new BuildScoreProvider() {
        @Override
        public boolean isExact() {
            return true;
        }

        @Override
        public VectorFloat<?> approximateCentroid() {
            var vectors = ravvSupplier.get();
            var centroid = vts.createFloatVector(vectors.dimension());

            for (int i = 0; i < vectors.size(); i++) {
                VectorUtil.addInPlace(centroid, vectors.vectorValue(i));
            }

            VectorUtil.scale(centroid, 1.0f / vectors.size());
            return centroid;
        }

        @Override
        public SearchScoreProvider searchProviderFor(VectorFloat<?> vector) {
            return SearchScoreProvider.exact(
                    vector, similarityFunction, ravvSupplier.get());
        }

        @Override
        public SearchScoreProvider searchProviderFor(int node1) {
            return searchProviderFor(ravvSupplier.get().vectorValue(node1));
        }

        @Override
        public SearchScoreProvider diversityProviderFor(int node1) {
            return searchProviderFor(node1);
        }
    };
}
```