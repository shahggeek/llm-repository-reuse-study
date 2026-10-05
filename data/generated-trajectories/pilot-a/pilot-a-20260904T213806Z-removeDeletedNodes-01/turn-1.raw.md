```java
public long removeDeletedNodes() {
    Set<Integer> deletedNodes = new HashSet<>(graph.getDeletedNodes());
    if (deletedNodes.isEmpty()) {
        return 0L;
    }

    for (int level = graph.layers.size() - 1; level >= 0; level--) {
        int[] liveNodes = graph.nodeStream(level)
                               .filter(node -> !deletedNodes.contains(node))
                               .toArray();

        for (int node : liveNodes) {
            Set<Integer> candidates = new HashSet<>();
            Set<Integer> visitedDeleted = new HashSet<>();
            Deque<Integer> pendingDeleted = new ArrayDeque<>();
            boolean hasDeletedNeighbor = false;

            var neighbors = graph.getNeighborsIterator(level, node);
            while (neighbors.hasNext()) {
                int neighbor = neighbors.nextInt();
                if (deletedNodes.contains(neighbor)) {
                    hasDeletedNeighbor = true;
                    if (visitedDeleted.add(neighbor)) {
                        pendingDeleted.addLast(neighbor);
                    }
                } else if (neighbor != node) {
                    candidates.add(neighbor);
                }
            }

            if (!hasDeletedNeighbor) {
                continue;
            }

            while (!pendingDeleted.isEmpty()) {
                int deleted = pendingDeleted.removeFirst();
                if (graph.getNeighbors(level, deleted) == null) {
                    continue;
                }

                var deletedNeighbors = graph.getNeighborsIterator(level, deleted);
                while (deletedNeighbors.hasNext()) {
                    int candidate = deletedNeighbors.nextInt();
                    if (candidate == node) {
                        continue;
                    }

                    if (deletedNodes.contains(candidate)) {
                        if (visitedDeleted.add(candidate)) {
                            pendingDeleted.addLast(candidate);
                        }
                    } else {
                        candidates.add(candidate);
                    }
                }
            }

            ScoreFunction scoreFunction =
                    scoreProvider.searchProviderFor(node).scoreFunction();
            NodeArray scoredCandidates = new NodeArray(candidates.size());
            for (int candidate : candidates) {
                scoredCandidates.insertSorted(
                        candidate, scoreFunction.similarityTo(candidate));
            }

            NodeArray newNeighbors =
                    graph.layers.get(level).insertDiverse(node, scoredCandidates);
            graph.layers.get(level)
                 .backlink(newNeighbors, node, neighborOverflow);
        }
    }

    for (int node : deletedNodes) {
        graph.removeNode(node);
    }

    return deletedNodes.size();
}
```