```java
public synchronized void writeInline(
        int ordinal, Map<FeatureId, Feature.State> stateMap) throws IOException {
    for (FeatureId featureId : stateMap.keySet()) {
        if (!featureMap.containsKey(featureId)) {
            throw new IllegalArgumentException("Feature not found: " + featureId);
        }
    }

    long position =
            startOffset
                    + headerSize
                    + (long) ordinal * layer0BlockSize
                    + Integer.BYTES;

    out.seek(position);

    for (Feature feature : inlineFeatures) {
        Feature.State state = stateMap.get(feature.id());
        if (state != null) {
            feature.writeInline(out, state);
        } else {
            out.seek(out.position() + feature.inlineSize());
        }
    }
}
```