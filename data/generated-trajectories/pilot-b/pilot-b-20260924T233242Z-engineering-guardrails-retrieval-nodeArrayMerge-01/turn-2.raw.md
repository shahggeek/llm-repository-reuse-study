```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    int size1 = a1.size();
    int size2 = a2.size();
    NodeArray merged = new NodeArray(size1 + size2);
    IntHashSet nodesAtCurrentScore = new IntHashSet();

    int i = 0;
    int j = 0;
    float currentScore = 0.0f;
    boolean hasCurrentScore = false;

    while (i < size1 || j < size2) {
        int node;
        float score;

        if (j >= size2 || (i < size1 && a1.scores[i] >= a2.scores[j])) {
            node = a1.nodes[i];
            score = a1.scores[i++];
        } else {
            node = a2.nodes[j];
            score = a2.scores[j++];
        }

        if (!hasCurrentScore || Float.compare(score, currentScore) != 0) {
            nodesAtCurrentScore.clear();
            currentScore = score;
            hasCurrentScore = true;
        }

        if (nodesAtCurrentScore.add(node)) {
            merged.addInOrder(node, score);
        }
    }

    return merged;
}
```