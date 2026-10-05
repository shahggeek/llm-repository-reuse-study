```java
public static List<Document> loadDocuments(Path directoryPath, DocumentParser documentParser){
    if (!isDirectory(directoryPath)) {
        throw illegalArgument("Illegal directoryPath.");
    }
    return new ArrayList<>();
}
```