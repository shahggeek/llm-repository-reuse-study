```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    int size1 = a1.size;
    int size2 = a2.size;
    NodeArray merged = new NodeArray(size1 + size2);
    IntHashSet seenAtScore = new IntHashSet();

    int i = 0;
    int j = 0;
    int dest = 0;

    while (i < size1 || j < size2) {
        float currentScore;
        if (j >= size2
                || (i < size1 && Float.compare(a1.scores[i], a2.scores[j]) >= 0)) {
            currentScore = a1.scores[i];
        } else {
            currentScore = a2.scores[j];
        }

        seenAtScore.clear();

        while ((i < size1 && Float.compare(a1.scores[i], currentScore) == 0)
                || (j < size2 && Float.compare(a2.scores[j], currentScore) == 0)) {
            int node;

            if (i < size1 && Float.compare(a1.scores[i], currentScore) == 0) {
                node = a1.nodes[i++];
            } else {
                node = a2.nodes[j++];
            }

            if (seenAtScore.add(node)) {
                merged.nodes[dest] = node;
                merged.scores[dest] = currentScore;
                dest++;
            }
        }
    }

    merged.size = dest;
    return merged;
}
```