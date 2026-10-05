```java
public static String methodToProperty(String name) {
    if (name == null || (!name.startsWith("get") && !name.startsWith("set"))) {
        throw new IllegalArgumentException(String.format(
                "Error parsing property name '%s'.  Didn't start with 'is', 'get' or 'set'.",
                name));
    }

    String property = name.substring(3);
    if (property.isEmpty()) {
        return property;
    }

    return Character.toLowerCase(property.charAt(0)) + property.substring(1);
}
```