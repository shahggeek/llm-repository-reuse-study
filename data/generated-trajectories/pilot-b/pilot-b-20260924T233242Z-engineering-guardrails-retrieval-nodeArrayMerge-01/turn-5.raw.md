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

    while (i < size1 && j < size2) {
        int node;
        float score;

        if (Float.compare(a1.scores[i], a2.scores[j]) >= 0) {
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

    int remainingIndex;
    int remainingSize;
    int[] remainingNodes;
    float[] remainingScores;

    if (i < size1) {
        remainingIndex = i;
        remainingSize = size1;
        remainingNodes = a1.nodes;
        remainingScores = a1.scores;
    } else {
        remainingIndex = j;
        remainingSize = size2;
        remainingNodes = a2.nodes;
        remainingScores = a2.scores;
    }

    while (remainingIndex < remainingSize
            && hasCurrentScore
            && Float.compare(remainingScores[remainingIndex], currentScore) == 0) {
        int node = remainingNodes[remainingIndex];
        if (nodesAtCurrentScore.add(node)) {
            merged.addInOrder(node, remainingScores[remainingIndex]);
        }
        remainingIndex++;
    }

    int remainingCount = remainingSize - remainingIndex;
    if (remainingCount > 0) {
        System.arraycopy(
                remainingNodes, remainingIndex, merged.nodes, merged.size, remainingCount);
        System.arraycopy(
                remainingScores, remainingIndex, merged.scores, merged.size, remainingCount);
        merged.size += remainingCount;
    }

    return merged;
}
```