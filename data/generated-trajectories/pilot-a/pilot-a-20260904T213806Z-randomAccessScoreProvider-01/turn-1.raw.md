```java
static BuildScoreProvider randomAccessScoreProvider(
        RandomAccessVectorValues ravv,
        VectorSimilarityFunction similarityFunction) {
    return new BuildScoreProvider() {
        @Override
        public boolean isExact() {
            return true;
        }

        @Override
        public VectorFloat<?> approximateCentroid() {
            VectorFloat<?> centroid = vts.createFloatVector(ravv.dimension());
            for (int i = 0; i < ravv.size(); i++) {
                VectorUtil.addInPlace(centroid, ravv.getVector(i));
            }
            VectorUtil.scale(centroid, 1.0f / ravv.size());
            return centroid;
        }

        @Override
        public SearchScoreProvider searchProviderFor(VectorFloat<?> vector) {
            return SearchScoreProvider.exact(vector, similarityFunction, ravv);
        }

        @Override
        public SearchScoreProvider searchProviderFor(int node1) {
            return searchProviderFor(ravv.getVector(node1));
        }

        @Override
        public SearchScoreProvider diversityProviderFor(int node1) {
            return searchProviderFor(node1);
        }
    };
}
```