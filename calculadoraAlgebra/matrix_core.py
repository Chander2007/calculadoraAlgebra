from fractions import Fraction


def fraction_to_str(frac):
    if isinstance(frac, Fraction):
        if frac.denominator == 1:
            return str(frac.numerator)
        else:
            return f"{frac.numerator}/{frac.denominator}"
    return str(frac)


class Matrix:
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if self.rows > 0 else 0
        self.shape = (self.rows, self.cols)

    def __getitem__(self, indices):
        i, j = indices
        return self.data[i][j]

    def __setitem__(self, indices, value):
        i, j = indices
        self.data[i][j] = value


def format_matrix_lines(matrix):
    if isinstance(matrix, Matrix):
        data = matrix.data
    else:
        data = matrix
    if not data:
        return ["[ ]"]
    str_rows = [[fraction_to_str(val) for val in row] for row in data]
    widths = [max(len(row[c]) for row in str_rows) for c in range(len(str_rows[0]))]
    lines = []
    for row in str_rows:
        padded = "  ".join(cell.rjust(widths[idx]) for idx, cell in enumerate(row))
        lines.append(f"[ {padded} ]")
    return lines


def _determinant_step(matrix):
    """Calcula determinante por reducción (sin pasos de UI)."""
    from fractions import Fraction
    n = len(matrix)
    mat = [row[:] for row in matrix]
    det = Fraction(1)
    for i in range(n):
        pivot = mat[i][i]
        if pivot == 0:
            for k in range(i+1, n):
                if mat[k][i] != 0:
                    mat[i], mat[k] = mat[k], mat[i]
                    det *= -1
                    pivot = mat[i][i]
                    break
        if pivot == 0:
            return Fraction(0)
        det *= pivot
        for j in range(i+1, n):
            factor = mat[j][i] / pivot
            for k in range(i, n):
                mat[j][k] -= factor * mat[i][k]
    return det


def _determinant_sarrus(matrix):
    """Calcula determinante 3x3 por Sarrus (puro, sin UI)."""
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    sum1 = a * e * i + b * f * g + c * d * h
    sum2 = c * e * g + b * d * i + a * f * h
    det = sum1 - sum2
    return det
