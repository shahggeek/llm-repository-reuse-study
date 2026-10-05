```java
public static List<Document> loadDocuments(Path directoryPath, DocumentParser documentParser){
    if (!Files.isDirectory(directoryPath)) {
        throw new IllegalArgumentException("Illegal directoryPath.");
    }
    return new ArrayList<>();
}
```