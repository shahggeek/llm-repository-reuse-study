```java
public long removeDeletedNodes() {
    Set<Integer> deletedNodes = new HashSet<>(graph.getDeletedNodes());
    if (deletedNodes.isEmpty()) {
        return 0L;
    }

    for (int level = graph.layers.size() - 1; level >= 0; level--) {
        ConcurrentHashMap<Integer, Set<Integer>> promotions =
                new ConcurrentHashMap<>();

        int currentLevel = level;
        parallelExecutor.submit(() ->
            graph.nodeStream(currentLevel)
                 .parallel()
                 .filter(node -> !deletedNodes.contains(node))
                 .forEach(node -> {
                     Set<Integer> promotedNeighbors = new HashSet<>();
                     boolean affected = false;

                     var neighbors =
                             graph.getNeighborsIterator(currentLevel, node);
                     while (neighbors.hasNext()) {
                         int neighbor = neighbors.nextInt();
                         if (!deletedNodes.contains(neighbor)) {
                             continue;
                         }

                         affected = true;
                         if (graph.getNeighbors(currentLevel, neighbor) == null) {
                             continue;
                         }

                         // FreshDiskANN edge promotion:
                         // (node, neighbor) and (neighbor, candidate)
                         // become (node, candidate) when neighbor is deleted.
                         var secondHop =
                                 graph.getNeighborsIterator(currentLevel, neighbor);
                         while (secondHop.hasNext()) {
                             int candidate = secondHop.nextInt();
                             if (candidate != node
                                     && !deletedNodes.contains(candidate)) {
                                 promotedNeighbors.add(candidate);
                             }
                         }
                     }

                     if (affected) {
                         promotions.put(node, promotedNeighbors);
                     }
                 })
        ).join();

        parallelExecutor.submit(() ->
            promotions.entrySet()
                      .parallelStream()
                      .forEach(entry -> {
                          int node = entry.getKey();
                          Set<Integer> candidates =
                                  new HashSet<>(entry.getValue());

                          var existing =
                                  graph.getNeighborsIterator(currentLevel, node);
                          while (existing.hasNext()) {
                              int candidate = existing.nextInt();
                              if (candidate != node
                                      && !deletedNodes.contains(candidate)) {
                                  candidates.add(candidate);
                              }
                          }

                          ScoreFunction scoreFunction =
                                  scoreProvider.searchProviderFor(node)
                                               .scoreFunction();
                          NodeArray scoredCandidates =
                                  new NodeArray(candidates.size());

                          for (int candidate : candidates) {
                              scoredCandidates.insertSorted(
                                      candidate,
                                      scoreFunction.similarityTo(candidate));
                          }

                          NodeArray newNeighbors =
                                  graph.layers.get(currentLevel)
                                              .insertDiverse(
                                                      node, scoredCandidates);
                          graph.layers.get(currentLevel)
                               .backlink(
                                       newNeighbors,
                                       node,
                                       neighborOverflow);
                      })
        ).join();
    }

    parallelExecutor.submit(() ->
        deletedNodes.parallelStream().forEach(graph::removeNode)
    ).join();

    return deletedNodes.size();
}
```