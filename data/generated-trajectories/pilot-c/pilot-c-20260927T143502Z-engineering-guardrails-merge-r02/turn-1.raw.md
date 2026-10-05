```java
public static <T> T merge(Object source, Object target, Class<T> clazz, List<String> acceptedFieldNames) {
	List<String> fieldNames = acceptedFieldNames != null
			? acceptedFieldNames
			: REQUEST_FIELD_NAMES_PER_CLASS.computeIfAbsent(clazz,
					type -> Arrays.stream(type.getDeclaredFields())
						.filter(field -> field.isAnnotationPresent(JsonProperty.class))
						.map(field -> {
							String name = field.getAnnotation(JsonProperty.class).value();
							return name.isEmpty() ? field.getName() : name;
						})
						.collect(Collectors.toList()));

	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = objectToMap(target);
	Map<String, Object> mergedMap = merge(sourceMap, targetMap, fieldNames);

	return mapToClass(mergedMap, clazz);
}
```