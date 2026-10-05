```java
private void encodeAnisotropic(VectorFloat<?> vector, ByteSequence<?> result) {
    float parallelResidual = 0.0f;

    for (int m = 0; m < M; m++) {
        int subvectorSize = subvectorSizesAndOffsets[m][0];
        int subvectorOffset = subvectorSizesAndOffsets[m][1];
        VectorFloat<?> codebook = codebooks[m];

        float bestDistance = Float.POSITIVE_INFINITY;
        int bestCentroid = 0;

        for (int centroid = 0; centroid < clusterCount; centroid++) {
            int centroidOffset = centroid * subvectorSize;
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

        int selectedCentroidOffset = bestCentroid * subvectorSize;
        parallelResidual += dotProduct(
                vector, subvectorOffset,
                vector, subvectorOffset,
                subvectorSize);
        parallelResidual -= dotProduct(
                vector, subvectorOffset,
                codebook, selectedCentroidOffset,
                subvectorSize);
    }

    for (int iteration = 0; iteration < 10; iteration++) {
        boolean centroidChanged = false;

        for (int m = 0; m < M; m++) {
            int currentCentroid = Byte.toUnsignedInt(result.get(m));
            float[] optimization = optimizeSingleSubspace(
                    vector, m, currentCentroid, parallelResidual);

            int newCentroid = (int) optimization[0];
            parallelResidual = optimization[1];

            if (newCentroid != currentCentroid) {
                result.set(m, (byte) newCentroid);
                centroidChanged = true;
            }
        }

        if (!centroidChanged) {
            break;
        }
    }
}
```