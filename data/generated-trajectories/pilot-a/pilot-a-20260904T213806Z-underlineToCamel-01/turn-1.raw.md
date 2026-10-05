```java
public static String underlineToCamel(String string) {
    if (string == null || string.isEmpty()) {
        return "";
    }

    StringBuilder result = new StringBuilder(string.length());
    boolean capitalizeNext = false;

    for (int i = 0; i < string.length(); i++) {
        char current = string.charAt(i);

        if (current == '_') {
            capitalizeNext = result.length() > 0;
        } else if (capitalizeNext) {
            result.append(Character.toUpperCase(current));
            capitalizeNext = false;
        } else {
            result.append(current);
        }
    }

    return result.toString();
}
```