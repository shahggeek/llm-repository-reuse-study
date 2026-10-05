```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    NodeArray merged = new NodeArray(a1.size + a2.size);
    IntHashSet nodesAtCurrentScore = new IntHashSet();

    int i = 0;
    int j = 0;
    float currentScore = 0.0f;
    boolean hasCurrentScore = false;

    while (i < a1.size || j < a2.size) {
        int node;
        float score;

        if (j >= a2.size || (i < a1.size && a1.scores[i] >= a2.scores[j])) {
            node = a1.nodes[i];
            score = a1.scores[i++];
        } else {
            node = a2.nodes[j];
            score = a2.scores[j++];
        }

        if (!hasCurrentScore || Float.compare(score, currentScore) != 0) {
            currentScore = score;
            hasCurrentScore = true;
            nodesAtCurrentScore.clear();
        }

        if (nodesAtCurrentScore.add(node)) {
            merged.nodes[merged.size] = node;
            merged.scores[merged.size] = score;
            merged.size++;
        }
    }

    return merged;
}
```