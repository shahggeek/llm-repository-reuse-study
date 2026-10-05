```java
static NodeArray merge(NodeArray a1, NodeArray a2) {
    NodeArray merged = new NodeArray(a1.size() + a2.size());
    int i = 0;
    int j = 0;

    while (i < a1.size() && j < a2.size()) {
        if (a1.scores[i] >= a2.scores[j]) {
            merged.addInOrder(a1.nodes[i], a1.scores[i]);
            i++;
        } else {
            merged.addInOrder(a2.nodes[j], a2.scores[j]);
            j++;
        }
    }

    while (i < a1.size()) {
        merged.addInOrder(a1.nodes[i], a1.scores[i]);
        i++;
    }

    while (j < a2.size()) {
        merged.addInOrder(a2.nodes[j], a2.scores[j]);
        j++;
    }

    return merged;
}
```