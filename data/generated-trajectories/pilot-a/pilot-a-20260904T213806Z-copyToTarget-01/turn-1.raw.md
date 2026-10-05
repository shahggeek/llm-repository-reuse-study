```java
<T, S extends T> T copyToTarget(S source, Class<T> sourceInterface, Class<T> targetClass) {
	if (source == null) {
		return null;
	}

	if (!sourceInterface.isInstance(source)) {
		throw new IllegalArgumentException("Source does not implement " + sourceInterface.getName());
	}

	try {
		T target = targetClass.getDeclaredConstructor().newInstance();
		BeanWrapper sourceWrapper = new BeanWrapperImpl(source);
		BeanWrapper targetWrapper = new BeanWrapperImpl(target);

		Arrays.stream(sourceWrapper.getPropertyDescriptors())
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