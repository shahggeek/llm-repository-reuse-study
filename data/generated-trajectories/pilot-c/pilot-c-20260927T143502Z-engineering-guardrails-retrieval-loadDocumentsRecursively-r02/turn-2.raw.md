```java
public static List<Document> loadDocumentsRecursively(Path directoryPath, DocumentParser documentParser) {
    if (directoryPath == null || !isDirectory(directoryPath)) {
        throw new IllegalArgumentException("The directoryPath you provided is illegal.");
    }

    try (Stream<Path> pathStream = Files.walk(directoryPath)) {
        return loadDocuments(pathStream, path -> true, directoryPath, documentParser);
    } catch (IOException | java.io.UncheckedIOException e) {
        throw new RuntimeException("Failed to traverse directory", e);
    }
}
```