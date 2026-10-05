```java
public static List<Document> loadDocumentsRecursively(Path directoryPath, DocumentParser documentParser) {
    if (!isDirectory(directoryPath)) {
        throw illegalArgument("'%s' is not a directory", directoryPath);
    }

    try (Stream<Path> pathStream = Files.walk(directoryPath)) {
        return loadDocuments(pathStream, path -> true, directoryPath, documentParser);
    } catch (IOException e) {
        throw new RuntimeException(e);
    }
}
```