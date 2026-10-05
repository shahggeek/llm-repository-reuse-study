```java
public static String underlineToCamel(String string) {
    StringBuilder result = new StringBuilder(string.length());

    for (int i = 0; i < string.length(); i++) {
        char current = string.charAt(i);
        if (current == '_') {
            current = Character.toUpperCase(string.charAt(++i));
        }
        result.append(current);
    }

    return result.toString();
}
```