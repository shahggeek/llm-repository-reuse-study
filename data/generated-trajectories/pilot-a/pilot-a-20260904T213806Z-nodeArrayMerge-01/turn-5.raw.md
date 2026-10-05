```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    NodeArray merged = new NodeArray(a1.size + a2.size);
    IntHashSet nodesAtCurrentScore = new IntHashSet();

    int i = 0;
    int j = 0;
    float lastScore = 0.0f;
    boolean hasLastScore = false;

    while (i < a1.size && j < a2.size) {
        int node;
        float score;

        if (Float.compare(a1.scores[i], a2.scores[j]) >= 0) {
            node = a1.nodes[i];
            score = a1.scores[i++];
        } else {
            node = a2.nodes[j];
            score = a2.scores[j++];
        }

        if (!hasLastScore || Float.compare(score, lastScore) != 0) {
            nodesAtCurrentScore.clear();
            lastScore = score;
            hasLastScore = true;
        }

        if (nodesAtCurrentScore.add(node)) {
            merged.nodes[merged.size] = node;
            merged.scores[merged.size] = score;
            merged.size++;
        }
    }

    NodeArray remaining = i < a1.size ? a1 : a2;
    int remainingIndex = i < a1.size ? i : j;

    while (remainingIndex < remaining.size
            && hasLastScore
            && Float.compare(remaining.scores[remainingIndex], lastScore) == 0) {
        int node = remaining.nodes[remainingIndex];

        if (nodesAtCurrentScore.add(node)) {
            merged.nodes[merged.size] = node;
            merged.scores[merged.size] = remaining.scores[remainingIndex];
            merged.size++;
        }

        remainingIndex++;
    }

    int remainingCount = remaining.size - remainingIndex;
    if (remainingCount > 0) {
        System.arraycopy(
                remaining.nodes, remainingIndex,
                merged.nodes, merged.size,
                remainingCount);
        System.arraycopy(
                remaining.scores, remainingIndex,
                merged.scores, merged.size,
                remainingCount);
        merged.size += remainingCount;
    }

    return merged;
}
```