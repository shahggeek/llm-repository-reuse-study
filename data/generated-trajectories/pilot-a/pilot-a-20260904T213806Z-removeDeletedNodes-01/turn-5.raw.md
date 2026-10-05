```java
public synchronized long removeDeletedNodes() {
    Set<Integer> deletedNodes = new HashSet<>(graph.getDeletedNodes());
    if (deletedNodes.isEmpty()) {
        return 0L;
    }

    long freedBytes = parallelExecutor.submit(() ->
        deletedNodes.parallelStream()
                    .mapToLong(node ->
                        IntStream.range(0, graph.layers.size())
                                 .filter(level ->
                                     graph.getNeighbors(level, node) != null)
                                 .mapToLong(graph::ramBytesUsedOneNode)
                                 .sum())
                    .sum()
    ).join();

    for (int level = graph.layers.size() - 1; level >= 0; level--) {
        int currentLevel = level;
        int[] liveNodes = graph.nodeStream(currentLevel)
                               .filter(node -> !deletedNodes.contains(node))
                               .toArray();

        ConcurrentHashMap<Integer, Set<Integer>> candidatesByNode =
                new ConcurrentHashMap<>();

        parallelExecutor.submit(() ->
            Arrays.stream(liveNodes).parallel().forEach(node -> {
                Set<Integer> candidates = new HashSet<>();
                boolean affected = false;

                var neighbors =
                        graph.getNeighborsIterator(currentLevel, node);
                while (neighbors.hasNext()) {
                    int neighbor = neighbors.nextInt();

                    if (!deletedNodes.contains(neighbor)) {
                        if (neighbor != node) {
                            candidates.add(neighbor);
                        }
                        continue;
                    }

                    affected = true;
                    if (graph.getNeighbors(currentLevel, neighbor) == null) {
                        continue;
                    }

                    var secondHop =
                            graph.getNeighborsIterator(currentLevel, neighbor);
                    while (secondHop.hasNext()) {
                        int candidate = secondHop.nextInt();
                        if (candidate != node
                                && !deletedNodes.contains(candidate)) {
                            candidates.add(candidate);
                        }
                    }
                }

                if (!affected) {
                    return;
                }

                if (candidates.isEmpty() && liveNodes.length > 1) {
                    int targetCount = Math.min(
                            graph.getDegree(currentLevel),
                            liveNodes.length - 1);
                    int start =
                            ThreadLocalRandom.current().nextInt(liveNodes.length);

                    for (int offset = 0;
                         offset < liveNodes.length
                                 && candidates.size() < targetCount;
                         offset++) {
                        int candidate =
                                liveNodes[(start + offset) % liveNodes.length];
                        if (candidate != node) {
                            candidates.add(candidate);
                        }
                    }
                }

                candidatesByNode.put(node, candidates);
            })
        ).join();

        parallelExecutor.submit(() ->
            candidatesByNode.entrySet().parallelStream().forEach(entry -> {
                int node = entry.getKey();
                Set<Integer> candidates = entry.getValue();

                ScoreFunction scoreFunction =
                        scoreProvider.searchProviderFor(node).scoreFunction();
                NodeArray scoredCandidates =
                        new NodeArray(candidates.size());

                for (int candidate : candidates) {
                    scoredCandidates.insertSorted(
                            candidate,
                            scoreFunction.similarityTo(candidate));
                }

                NodeArray newNeighbors =
                        graph.layers.get(currentLevel)
                                    .insertDiverse(node, scoredCandidates);

                graph.layers.get(currentLevel)
                            .backlink(newNeighbors, node, neighborOverflow);
            })
        ).join();
    }

    NodeAtLevel entry = graph.entry();
    if (entry != null && deletedNodes.contains(entry.node)) {
        NodeAtLevel replacement = null;

        for (int level = graph.layers.size() - 1;
             level >= 0 && replacement == null;
             level--) {
            OptionalInt candidate =
                    graph.nodeStream(level)
                         .filter(node -> !deletedNodes.contains(node))
                         .findAny();

            if (candidate.isPresent()) {
                replacement = new NodeAtLevel(level, candidate.getAsInt());
            }
        }

        if (replacement != null) {
            graph.updateEntryNode(replacement);
        }
    }

    for (int node : deletedNodes) {
        graph.removeNode(node);
    }

    return freedBytes;
}
```