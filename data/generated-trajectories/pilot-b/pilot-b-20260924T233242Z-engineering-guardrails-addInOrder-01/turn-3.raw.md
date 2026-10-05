```java
public void addInOrder(int newNode, float newScore) {
    if (size == nodes.length) {
        growArrays();
    }

    assert size == 0 || newScore <= scores[size - 1];

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;
}
```