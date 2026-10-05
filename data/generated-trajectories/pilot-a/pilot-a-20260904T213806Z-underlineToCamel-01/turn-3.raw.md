```java
public static String underlineToCamel(String string) {
    StringBuilder result = new StringBuilder(string.length());

    for (int i = 0; i < string.length(); i++) {
        char current = string.charAt(i);

        if (i == 0) {
            current = Character.toLowerCase(current);
        }

        if (current == '_') {
            if (i + 1 < string.length() && string.charAt(i + 1) != '_') {
                result.append(Character.toUpperCase(string.charAt(++i)));
            }
        } else {
            result.append(current);
        }
    }

    return result.toString();
}
```