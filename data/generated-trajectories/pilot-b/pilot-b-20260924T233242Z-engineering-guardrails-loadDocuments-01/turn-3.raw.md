```java
public static List<Document> loadDocuments(Path directoryPath, DocumentParser documentParser){
    if (!isDirectory(directoryPath)) {
        throw illegalArgument("Illegal directoryPath.");
    }

    try (Stream<Path> pathStream = Files.list(directoryPath)) {
        return loadDocuments(pathStream, path -> true, directoryPath, documentParser);
    } catch (IOException e) {
        throw new RuntimeException("Runtime error", e);
    }
}
```