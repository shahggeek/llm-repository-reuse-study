```java
public void addInOrder(int newNode, float newScore) {
    if (size == nodes.length) {
        growArrays();
    }

    assert size == 0 || newScore <= scores[size - 1]
            : "Scores are not in descending order: new score "
                    + newScore
                    + ", existing scores "
                    + Arrays.toString(ArrayUtil.copyOfSubArray(scores, 0, size));

    nodes[size] = newNode;
    scores[size] = newScore;
    size++;
}
```