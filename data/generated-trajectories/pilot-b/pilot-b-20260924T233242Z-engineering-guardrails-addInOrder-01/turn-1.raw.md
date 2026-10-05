```java
public void addInOrder(int newNode, float newScore) {
    if (size == nodes.length) {
        nodes = ArrayUtil.grow(nodes);
        scores = ArrayUtil.grow(scores);
    }

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;
}
```