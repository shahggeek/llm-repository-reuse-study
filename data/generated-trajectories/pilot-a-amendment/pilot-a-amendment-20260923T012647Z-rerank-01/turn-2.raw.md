```java
public float rerank(
        int topK,
        ScoreFunction.Reranker reranker,
        float rerankFloor,
        Int2ObjectHashMap<Float> reranked,
        Int2ObjectHashMap<Float> unused) {
    reranked.clear();
    unused.clear();

    var originalScores = new Int2ObjectHashMap<Float>();

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

    while (size() > 0) {
        long value = heap.pop();
        int node = decodeNodeId(value);
        float approximateScore = decodeScore(value);

        if (approximateScore < rerankFloor) {
            unused.put(node, approximateScore);
            continue;
        }

        float exactScore = reranker.similarityTo(node);
        originalScores.put(node, approximateScore);
        best.push(node, exactScore);
    }

    int rerankedCount = best.size();
    float worstApproximateScore = Float.POSITIVE_INFINITY;

    while (best.size() > 0) {
        long value = best.heap.pop();
        int node = best.decodeNodeId(value);
        float exactScore = best.decodeScore(value);
        float approximateScore = originalScores.remove(node);

        reranked.put(node, exactScore);
        worstApproximateScore = min(worstApproximateScore, approximateScore);
    }

    unused.putAll(originalScores);

    return rerankedCount < topK
            ? Float.POSITIVE_INFINITY
            : worstApproximateScore;
}
```