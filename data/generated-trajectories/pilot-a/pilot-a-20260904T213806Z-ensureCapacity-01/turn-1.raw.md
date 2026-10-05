```java
public static FixedBitSet ensureCapacity(FixedBitSet bits, int numBits) {
    if (numBits < bits.numBits) {
        return bits;
    }

    int numWords = bits2words(numBits);
    long[] newBits = bits.getBits();

    if (numWords >= newBits.length) {
        newBits = ArrayUtil.grow(newBits, numWords + 1);
    }

    return new FixedBitSet(newBits, newBits.length << 6);
}
```