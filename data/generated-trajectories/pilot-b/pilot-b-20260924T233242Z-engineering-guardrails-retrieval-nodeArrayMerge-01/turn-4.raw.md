```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    int size1 = a1.size();
    int size2 = a2.size();
    NodeArray merged = new NodeArray(size1 + size2);
    IntHashSet nodesAtCurrentScore = new IntHashSet();

    int i = 0;
    int j = 0;

    while (i < size1 || j < size2) {
        float currentScore;
        if (j >= size2
                || (i < size1 && Float.compare(a1.scores[i], a2.scores[j]) >= 0)) {
            currentScore = a1.scores[i];
        } else {
            currentScore = a2.scores[j];
        }

        nodesAtCurrentScore.clear();

        while (i < size1 && Float.compare(a1.scores[i], currentScore) == 0) {
            if (nodesAtCurrentScore.add(a1.nodes[i])) {
                merged.addInOrder(a1.nodes[i], a1.scores[i]);
            }
            i++;
        }

        while (j < size2 && Float.compare(a2.scores[j], currentScore) == 0) {
            if (nodesAtCurrentScore.add(a2.nodes[j])) {
                merged.addInOrder(a2.nodes[j], a2.scores[j]);
            }
            j++;
        }
    }

    return merged;
}
```