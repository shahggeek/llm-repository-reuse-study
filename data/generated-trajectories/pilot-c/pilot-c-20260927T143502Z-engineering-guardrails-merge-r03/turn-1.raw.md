```java
public static <T> T merge(Object source, Object target, Class<T> clazz, List<String> acceptedFieldNames) {
	Map<String, Object> sourceMap = objectToMap(source);
	Map<String, Object> targetMap = objectToMap(target);

	List<String> fieldNames = acceptedFieldNames != null
			? acceptedFieldNames
			: getJsonPropertyValues(clazz);

	Map<String, Object> mergedMap = merge(sourceMap, targetMap, fieldNames);
	return mapToClass(mergedMap, clazz);
}
```