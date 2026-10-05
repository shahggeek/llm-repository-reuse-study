```java
public static List<Document> loadDocuments(Path directoryPath, DocumentParser documentParser) {
    if (!isDirectory(directoryPath)) {
        throw new IllegalArgumentException("Illegal directoryPath.");
    }
    return new ArrayList<>();
}
```