```java
public void addInOrder(int newNode, float newScore) {
    if (size == nodes.length) {
        growArrays();
    }

    if (size > 0) {
        assert newScore <= scores[size - 1];
    }

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;
}
```