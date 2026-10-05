```java
public static <T> T merge(Object source, Object target, Class<T> clazz, List<String> acceptedFieldNames) {
	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = objectToMap(target);

	List<String> fieldNames = acceptedFieldNames != null
			? acceptedFieldNames
			: REQUEST_FIELD_NAMES_PER_CLASS.computeIfAbsent(clazz, ModelOptionsUtils::getJsonPropertyValues);

	if (fieldNames.isEmpty()) {
		throw new IllegalArgumentException(
				"Class " + clazz.getName() + " has no fields annotated with @JsonProperty");
	}

	Map<String, Object> mergedMap = merge(sourceMap, targetMap, fieldNames);
	return mapToClass(mergedMap, clazz);
}
```