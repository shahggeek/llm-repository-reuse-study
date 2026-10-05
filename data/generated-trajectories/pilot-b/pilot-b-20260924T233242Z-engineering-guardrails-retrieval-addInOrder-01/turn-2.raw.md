```java
public void addInOrder(int newNode, float newScore) {
    if (size == nodes.length) {
        growArrays();
    }

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;

    assert size == 1 || scores[size - 2] >= scores[size - 1]
            : "Scores are not in descending order: "
                    + Arrays.toString(ArrayUtil.copyOfSubArray(scores, 0, size));
}
```