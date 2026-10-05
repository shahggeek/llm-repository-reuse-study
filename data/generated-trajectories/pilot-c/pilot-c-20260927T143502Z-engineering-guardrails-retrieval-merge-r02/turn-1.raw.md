```java
public static <T> T merge(Object source, Object target, Class<T> clazz, List<String> acceptedFieldNames) {
	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = new HashMap<>(objectToMap(target));

	List<String> fieldNames = !CollectionUtils.isEmpty(acceptedFieldNames)
			? acceptedFieldNames
			: REQUEST_FIELD_NAMES_PER_CLASS.computeIfAbsent(clazz, ModelOptionsUtils::getJsonPropertyValues);

	sourceMap.forEach((fieldName, value) -> {
		if (fieldNames.contains(fieldName)) {
			targetMap.put(fieldName, value);
		}
	});

	return mapToClass(targetMap, clazz);
}
```