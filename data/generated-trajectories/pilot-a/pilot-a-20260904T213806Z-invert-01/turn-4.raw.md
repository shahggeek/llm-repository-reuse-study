```java
public Matrix invert() {
    int rows = data.length;
    int columns = rows == 0 ? 0 : data[0].length();

    if (rows != columns) {
        throw new IllegalArgumentException("matrix must be square");
    }

    int n = rows;
    Matrix augmented = new Matrix(n, 2 * n);
    final float singularityThreshold = 1.0e-8f;

    // Append the identity matrix to the original matrix.
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            augmented.set(i, j, get(i, j));
            augmented.set(i, n + j, i == j ? 1.0f : 0.0f);
        }
    }

    // Perform Gaussian elimination with partial pivoting.
    for (int column = 0; column < n; column++) {
        int pivotRow = column;
        float largestValue = abs(augmented.get(column, column));

        for (int row = column + 1; row < n; row++) {
            float value = abs(augmented.get(row, column));
            if (value > largestValue) {
                largestValue = value;
                pivotRow = row;
            }
        }

        if (largestValue <= singularityThreshold) {
            throw new IllegalArgumentException("matrix is singular and cannot be inverted");
        }

        if (pivotRow != column) {
            VectorFloat<?> temporary = augmented.data[column];
            augmented.data[column] = augmented.data[pivotRow];
            augmented.data[pivotRow] = temporary;
        }

        float pivot = augmented.get(column, column);
        for (int j = 0; j < 2 * n; j++) {
            augmented.set(column, j, augmented.get(column, j) / pivot);
        }

        for (int row = 0; row < n; row++) {
            if (row == column) {
                continue;
            }

            float factor = augmented.get(row, column);
            for (int j = 0; j < 2 * n; j++) {
                augmented.set(
                        row,
                        j,
                        augmented.get(row, j) - factor * augmented.get(column, j));
            }
        }
    }

    // Extract the inverse from the right half.
    Matrix inverse = new Matrix(n, n);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            inverse.set(i, j, augmented.get(i, n + j));
        }
    }

    return inverse;
}
```