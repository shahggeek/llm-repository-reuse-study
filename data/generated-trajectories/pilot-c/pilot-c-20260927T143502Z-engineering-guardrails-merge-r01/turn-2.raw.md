```java
public static <T> T merge(Object source, Object target, Class<T> clazz, List<String> acceptedFieldNames) {
	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = objectToMap(target);

	List<String> fieldNames = acceptedFieldNames;
	if (CollectionUtils.isEmpty(fieldNames)) {
		fieldNames = REQUEST_FIELD_NAMES_PER_CLASS.computeIfAbsent(clazz,
				type -> Arrays.stream(type.getDeclaredFields())
					.filter(field -> field.isAnnotationPresent(JsonProperty.class))
					.map(field -> field.getAnnotation(JsonProperty.class).value())
					.collect(Collectors.toList()));
	}

	if (fieldNames.isEmpty()) {
		throw new IllegalArgumentException(
				"Class " + clazz.getName() + " has no fields annotated with @JsonProperty");
	}

	Map<String, Object> mergedMap = mergeMaps(sourceMap, targetMap, fieldNames);
	return mapToClass(mergedMap, clazz);
}
```