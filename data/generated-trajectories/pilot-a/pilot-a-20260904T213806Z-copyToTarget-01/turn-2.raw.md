```java
<T, S extends T> T copyToTarget(S source, Class<T> sourceInterface, Class<T> targetClass) {
	if (source == null) {
		return null;
	}

	if (!sourceInterface.isInstance(source)) {
		throw new IllegalArgumentException("Source does not implement " + sourceInterface.getName());
	}

	List<String> getterMethodNames = Arrays.stream(sourceInterface.getMethods())
		.filter(method -> method.getParameterCount() == 0)
		.filter(method -> method.getReturnType() != Void.TYPE)
		.filter(method -> method.getName().startsWith("get")
				|| (method.getName().startsWith("is")
						&& (method.getReturnType() == boolean.class || method.getReturnType() == Boolean.class)))
		.map(method -> method.getName())
		.toList();

	try {
		T target = targetClass.getDeclaredConstructor().newInstance();
		BeanWrapper sourceWrapper = new BeanWrapperImpl(source);
		BeanWrapper targetWrapper = new BeanWrapperImpl(target);

		Arrays.stream(sourceWrapper.getPropertyDescriptors())
			.filter(descriptor -> descriptor.getReadMethod() != null)
			.filter(descriptor -> getterMethodNames.contains(descriptor.getReadMethod().getName()))
			.map(PropertyDescriptor::getName)
			.filter(name -> !BEAN_MERGE_FIELD_EXCISIONS.contains(name))
			.filter(sourceWrapper::isReadableProperty)
			.filter(targetWrapper::isWritableProperty)
			.forEach(name -> targetWrapper.setPropertyValue(name, sourceWrapper.getPropertyValue(name)));

		return target;
	}
	catch (ReflectiveOperationException e) {
		throw new IllegalArgumentException("Unable to instantiate target class " + targetClass.getName(), e);
	}
}
```