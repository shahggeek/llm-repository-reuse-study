```java
public static <T> T merge(Object source, Object target, Class<T> clazz, List<String> acceptedFieldNames) {
	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = objectToMap(target);

	List<String> fieldNames = CollectionUtils.isEmpty(acceptedFieldNames)
			? REQUEST_FIELD_NAMES_PER_CLASS.computeIfAbsent(clazz, ModelOptionsUtils::getJsonPropertyValues)
			: acceptedFieldNames;

	if (fieldNames.isEmpty()) {
		throw new IllegalArgumentException(
				"Class " + clazz.getName() + " has no fields annotated with @JsonProperty");
	}

	Map<String, Object> filteredSourceMap = sourceMap.entrySet()
		.stream()
		.filter(entry -> fieldNames.contains(entry.getKey()))
		.collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));

	targetMap.putAll(filteredSourceMap);
	return mapToClass(targetMap, clazz);
}
```