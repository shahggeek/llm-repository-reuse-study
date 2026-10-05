```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    NodeArray merged = new NodeArray(a1.size + a2.size);

    int i = 0;
    int j = 0;
    int k = 0;

    while (i < a1.size && j < a2.size) {
        if (a1.scores[i] >= a2.scores[j]) {
            merged.nodes[k] = a1.nodes[i];
            merged.scores[k] = a1.scores[i];
            i++;
        } else {
            merged.nodes[k] = a2.nodes[j];
            merged.scores[k] = a2.scores[j];
            j++;
        }
        k++;
    }

    int remainingA = a1.size - i;
    if (remainingA > 0) {
        System.arraycopy(a1.nodes, i, merged.nodes, k, remainingA);
        System.arraycopy(a1.scores, i, merged.scores, k, remainingA);
        k += remainingA;
    }

    int remainingB = a2.size - j;
    if (remainingB > 0) {
        System.arraycopy(a2.nodes, j, merged.nodes, k, remainingB);
        System.arraycopy(a2.scores, j, merged.scores, k, remainingB);
        k += remainingB;
    }

    merged.size = k;
    return merged;
}
```