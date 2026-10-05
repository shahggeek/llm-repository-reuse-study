```java
public static <I, T, S extends T> T mergeBeans(S source, T target, Class<I> sourceInterfaceClazz,
		boolean overrideNonNullTargetValues) {
	Assert.notNull(source, "Source bean must not be null");
	Assert.notNull(target, "Target bean must not be null");
	Assert.notNull(sourceInterfaceClazz, "Source interface class must not be null");
	Assert.isTrue(sourceInterfaceClazz.isInterface(), "Source class must be an interface");

	BeanWrapper sourceWrapper = new BeanWrapperImpl(source);
	BeanWrapper targetWrapper = new BeanWrapperImpl(target);

	List<String> interfaceGetterNames = Arrays.stream(sourceInterfaceClazz.getMethods())
		.filter(method -> method.getParameterCount() == 0)
		.filter(method -> method.getReturnType() != Void.TYPE)
		.filter(method -> method.getName().startsWith("get")
				|| (method.getName().startsWith("is")
						&& (method.getReturnType() == boolean.class
								|| method.getReturnType() == Boolean.class)))
		.map(method -> method.getName())
		.toList();

	for (PropertyDescriptor descriptor : sourceWrapper.getPropertyDescriptors()) {
		String propertyName = descriptor.getName();

		if (descriptor.getReadMethod() == null
				|| !interfaceGetterNames.contains(descriptor.getReadMethod().getName())
				|| !sourceWrapper.isReadableProperty(propertyName)
				|| !targetWrapper.isWritableProperty(propertyName)) {
			continue;
		}

		Object sourceValue = sourceWrapper.getPropertyValue(propertyName);
		if (sourceValue == null) {
			continue;
		}

		if (!overrideNonNullTargetValues
				&& targetWrapper.isReadableProperty(propertyName)
				&& targetWrapper.getPropertyValue(propertyName) != null) {
			continue;
		}

		targetWrapper.setPropertyValue(propertyName, sourceValue);
	}

	return target;
}
```