```java
public static FixedBitSet ensureCapacity(FixedBitSet bits, int numBits) {
    if (numBits < bits.numBits) {
        return bits;
    }

    int numWords = bits2words(numBits);
    long[] backingArray = bits.getBits();

    if (numWords >= backingArray.length) {
        // ArrayUtil.grow copies existing words and zero-initializes all new words.
        backingArray = ArrayUtil.grow(backingArray, numWords + 1);
    }

    return new FixedBitSet(backingArray, backingArray.length << 6);
}
```