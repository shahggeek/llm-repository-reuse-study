```java
public static <T> T merge(Object source, Object target, Class<T> clazz,List<String>acceptedFieldNames){
	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = objectToMap(target);
	Map<String, Object> mergedMap = merge(sourceMap, targetMap);

	List<String> fieldNames = CollectionUtils.isEmpty(acceptedFieldNames)
			? REQUEST_FIELD_NAMES_PER_CLASS.computeIfAbsent(clazz, ModelOptionsUtils::getJsonPropertyValues)
			: acceptedFieldNames;

	Map<String, Object> filteredMap = mergedMap.entrySet()
		.stream()
		.filter(entry -> fieldNames.contains(entry.getKey()))
		.collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));

	return mapToClass(filteredMap, clazz);
}
```