```java
public synchronized void writeInline(
        int ordinal, Map<FeatureId, Feature.State> stateMap) throws IOException {
    for (FeatureId featureId : stateMap.keySet()) {
        if (!featureMap.containsKey(featureId)) {
            throw new IllegalArgumentException("Feature not found: " + featureId);
        }
    }

    out.seek(featureOffsetForOrdinal(ordinal));

    for (Feature feature : inlineFeatures) {
        Feature.State state = stateMap.get(feature.id());
        if (state != null) {
            feature.writeInline(out, state);
        } else {
            out.seek(out.position() + feature.inlineSize());
        }
    }

    maxOrdinal = Math.max(maxOrdinal, ordinal);
}
```