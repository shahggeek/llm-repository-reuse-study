```java
public static FixedBitSet ensureCapacity(FixedBitSet bits, int numBits) {
    if (numBits < bits.numBits) {
        return bits;
    }

    int numWords = bits2words(numBits);
    long[] words = bits.getBits();
    if (numWords >= words.length) {
        // Arrays.copyOf preserves existing words and zero-initializes all newly allocated words.
        words = Arrays.copyOf(words, numWords + 1);
    }

    // FixedBitSet maintains clear ghost bits, so extending the logical capacity is safe.
    return new FixedBitSet(words, words.length << 6);
}
```