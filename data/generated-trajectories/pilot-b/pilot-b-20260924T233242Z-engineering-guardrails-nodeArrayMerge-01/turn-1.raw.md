```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    int size1 = a1.size;
    int size2 = a2.size;
    NodeArray merged = new NodeArray(size1 + size2);

    int i = 0;
    int j = 0;
    int dest = 0;

    while (i < size1 && j < size2) {
        if (Float.compare(a1.scores[i], a2.scores[j]) >= 0) {
            merged.nodes[dest] = a1.nodes[i];
            merged.scores[dest] = a1.scores[i];
            i++;
        } else {
            merged.nodes[dest] = a2.nodes[j];
            merged.scores[dest] = a2.scores[j];
            j++;
        }
        dest++;
    }

    if (i < size1) {
        int remaining = size1 - i;
        System.arraycopy(a1.nodes, i, merged.nodes, dest, remaining);
        System.arraycopy(a1.scores, i, merged.scores, dest, remaining);
        dest += remaining;
    } else if (j < size2) {
        int remaining = size2 - j;
        System.arraycopy(a2.nodes, j, merged.nodes, dest, remaining);
        System.arraycopy(a2.scores, j, merged.scores, dest, remaining);
        dest += remaining;
    }

    merged.size = dest;
    return merged;
}
```