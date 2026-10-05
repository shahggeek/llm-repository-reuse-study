```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    NodeArray merged = new NodeArray(a1.size + a2.size);
    IntHashSet nodesAtCurrentScore = new IntHashSet();

    int i = 0;
    int j = 0;

    while (i < a1.size || j < a2.size) {
        boolean scoreComesFromA = i < a1.size
                && (j >= a2.size
                || Float.compare(a1.scores[i], a2.scores[j]) >= 0);

        float currentScore = scoreComesFromA
                ? a1.scores[i]
                : a2.scores[j];

        nodesAtCurrentScore.clear();

        while (i < a1.size
                && Float.compare(a1.scores[i], currentScore) == 0) {
            if (nodesAtCurrentScore.add(a1.nodes[i])) {
                merged.nodes[merged.size] = a1.nodes[i];
                merged.scores[merged.size] = a1.scores[i];
                merged.size++;
            }
            i++;
        }

        while (j < a2.size
                && Float.compare(a2.scores[j], currentScore) == 0) {
            if (nodesAtCurrentScore.add(a2.nodes[j])) {
                merged.nodes[merged.size] = a2.nodes[j];
                merged.scores[merged.size] = a2.scores[j];
                merged.size++;
            }
            j++;
        }
    }

    return merged;
}
```