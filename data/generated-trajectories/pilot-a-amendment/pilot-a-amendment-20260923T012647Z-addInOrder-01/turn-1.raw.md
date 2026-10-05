```java
public void addInOrder(int newNode, float newScore) {
    if (size > 0 && scores[size - 1] < newScore) {
        throw new IllegalArgumentException("Nodes must be added in descending score order");
    }

    if (size == nodes.length) {
        int newCapacity = Math.max(1, nodes.length + (nodes.length >> 1));
        nodes = Arrays.copyOf(nodes, newCapacity);
        scores = Arrays.copyOf(scores, newCapacity);
    }

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;
}
```