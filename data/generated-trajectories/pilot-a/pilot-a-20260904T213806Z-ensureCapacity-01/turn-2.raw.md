```java
public static FixedBitSet ensureCapacity(FixedBitSet bits, int numBits) {
    if (numBits < bits.numBits) {
        return bits;
    }

    int numWords = bits2words(numBits);
    long[] backingArray = bits.getBits();

    if (numWords >= backingArray.length) {
        backingArray = Arrays.copyOf(backingArray, numWords + 1);
    }

    return new FixedBitSet(backingArray, backingArray.length << 6);
}
```