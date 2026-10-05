```java
public static List<Document> loadDocuments(Path directoryPath, DocumentParser documentParser) {
    List<Document> documents = new ArrayList<>();

    try (Stream<Path> paths = Files.list(directoryPath)) {
        paths.filter(Files::isRegularFile).forEach(path -> {
            try {
                documents.add(loadDocument(path, documentParser));
            } catch (Exception e) {
                // Skip files that cannot be parsed.
            }
        });
    } catch (IOException e) {
        throw new RuntimeException("Runtime error", e);
    }

    return documents;
}
```