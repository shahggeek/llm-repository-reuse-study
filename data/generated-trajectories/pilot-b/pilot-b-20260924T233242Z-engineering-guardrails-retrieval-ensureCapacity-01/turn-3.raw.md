```java
public static FixedBitSet ensureCapacity(FixedBitSet bits, int numBits) {
    if (numBits < bits.numBits) {
        return bits;
    }

    int numWords = bits2words(numBits);
    long[] words = bits.getBits();
    if (numWords >= words.length) {
        words = ArrayUtil.grow(words, numWords + 1);
    }

    return new FixedBitSet(words, words.length << 6);
}
```