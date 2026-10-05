```java
public void addInOrder(int newNode, float newScore) {
    if (size == nodes.length) {
        growArrays();
    }

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;
}
```