```java
public float rerank(
        int topK,
        ScoreFunction.Reranker reranker,
        float rerankFloor,
        Int2ObjectHashMap<Float> reranked,
        Int2ObjectHashMap<Float> unused) {
    reranked.clear();
    unused.clear();

    var approximateScores = new Int2ObjectHashMap<Float>();

    if (topK <= 0) {
        while (size() > 0) {
            long value = heap.pop();
            unused.put(decodeNodeId(value), decodeScore(value));
        }
        return Float.POSITIVE_INFINITY;
    }

    var best = new NodeQueue(
            new BoundedLongHeap(min(topK, size())),
            Order.MIN_HEAP);

    boolean foundAboveFloor = false;
    int fallbackNode = -1;
    float fallbackScore = Float.NEGATIVE_INFINITY;

    while (size() > 0) {
        long value = heap.pop();
        int node = decodeNodeId(value);
        float approximateScore = decodeScore(value);

        if (fallbackNode < 0
                || Float.compare(approximateScore, fallbackScore) > 0
                || (Float.compare(approximateScore, fallbackScore) == 0
                        && node < fallbackNode)) {
            fallbackNode = node;
            fallbackScore = approximateScore;
        }

        if (approximateScore < rerankFloor) {
            unused.put(node, approximateScore);
            continue;
        }

        foundAboveFloor = true;
        approximateScores.put(node, approximateScore);
        best.push(node, reranker.similarityTo(node));
    }

    if (!foundAboveFloor && fallbackNode >= 0) {
        unused.remove(fallbackNode);
        approximateScores.put(fallbackNode, fallbackScore);
        best.push(fallbackNode, reranker.similarityTo(fallbackNode));
    }

    int rerankedCount = best.size();
    float worstApproximateScore = Float.POSITIVE_INFINITY;

    while (best.size() > 0) {
        long value = best.heap.pop();
        int node = best.decodeNodeId(value);
        float exactScore = best.decodeScore(value);
        float approximateScore = approximateScores.remove(node);

        reranked.put(node, exactScore);
        worstApproximateScore = min(worstApproximateScore, approximateScore);
    }

    unused.putAll(approximateScores);

    return rerankedCount < topK
            ? Float.POSITIVE_INFINITY
            : worstApproximateScore;
}
```