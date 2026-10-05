```java
public static String methodToProperty(String name) {
    if (name == null) {
        throw new IllegalArgumentException(String.format(
                "Error parsing property name '%s'.  Didn't start with 'is', 'get' or 'set'.",
                name));
    }

    String property;
    if (name.startsWith("is")) {
        property = name.substring(2);
    } else if (name.startsWith("get") || name.startsWith("set")) {
        property = name.substring(3);
    } else {
        throw new IllegalArgumentException(String.format(
                "Error parsing property name '%s'.  Didn't start with 'is', 'get' or 'set'.",
                name));
    }

    if (property.isEmpty()) {
        return property;
    }

    return property.substring(0, 1).toLowerCase(Locale.ENGLISH)
            + property.substring(1);
}
```