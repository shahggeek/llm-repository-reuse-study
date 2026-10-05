```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    int size1 = a1.size;
    int size2 = a2.size;
    NodeArray merged = new NodeArray(size1 + size2);
    IntHashSet seenAtScore = new IntHashSet();

    int i = 0;
    int j = 0;
    int dest = 0;
    float lastScore = 0.0f;
    boolean hasLastScore = false;

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

        if (!hasLastScore || Float.compare(score, lastScore) != 0) {
            seenAtScore.clear();
            lastScore = score;
            hasLastScore = true;
        }

        if (seenAtScore.add(node)) {
            merged.nodes[dest] = node;
            merged.scores[dest] = score;
            dest++;
        }
    }

    int[] remainingNodes;
    float[] remainingScores;
    int remainingIndex;
    int remainingSize;

    if (i < size1) {
        remainingNodes = a1.nodes;
        remainingScores = a1.scores;
        remainingIndex = i;
        remainingSize = size1;
    } else {
        remainingNodes = a2.nodes;
        remainingScores = a2.scores;
        remainingIndex = j;
        remainingSize = size2;
    }

    if (hasLastScore) {
        while (remainingIndex < remainingSize
                && Float.compare(remainingScores[remainingIndex], lastScore) == 0) {
            int node = remainingNodes[remainingIndex];
            if (seenAtScore.add(node)) {
                merged.nodes[dest] = node;
                merged.scores[dest] = remainingScores[remainingIndex];
                dest++;
            }
            remainingIndex++;
        }
    }

    int remaining = remainingSize - remainingIndex;
    if (remaining > 0) {
        System.arraycopy(remainingNodes, remainingIndex, merged.nodes, dest, remaining);
        System.arraycopy(remainingScores, remainingIndex, merged.scores, dest, remaining);
        dest += remaining;
    }

    merged.size = dest;
    return merged;
}
```