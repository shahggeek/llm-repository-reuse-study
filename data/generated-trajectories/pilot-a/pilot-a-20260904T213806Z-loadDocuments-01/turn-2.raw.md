```java
public static List<Document> loadDocuments(Path directoryPath, DocumentParser documentParser) {
    try (Stream<Path> paths = Files.list(directoryPath)) {
        return paths.filter(Files::isRegularFile)
                .map(path -> loadDocument(path, documentParser))
                .collect(java.util.stream.Collectors.toList());
    } catch (IOException e) {
        throw new RuntimeException(e);
    }
}
```