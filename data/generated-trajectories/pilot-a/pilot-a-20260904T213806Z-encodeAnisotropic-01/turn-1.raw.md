```java
private void encodeAnisotropic(VectorFloat<?> vector, ByteSequence<?> result) {
    for (int m = 0; m < M; m++) {
        int subvectorSize = subvectorSizesAndOffsets[m][0];
        int subvectorOffset = subvectorSizesAndOffsets[m][1];
        VectorFloat<?> codebook = codebooks[m];

        float bestDistance = Float.POSITIVE_INFINITY;
        int bestCentroid = 0;

        for (int centroid = 0; centroid < clusterCount; centroid++) {
            int centroidOffset = centroid * subvectorSize;

            // The subvector's squared norm is constant across centroids.
            float distance = centroidNormsSquared[m][centroid]
                    - 2.0f * dotProduct(
                            vector, subvectorOffset,
                            codebook, centroidOffset,
                            subvectorSize);

            if (distance < bestDistance) {
                bestDistance = distance;
                bestCentroid = centroid;
            }
        }

        result.set(m, (byte) bestCentroid);
    }
}
```