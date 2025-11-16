from matrix_core import Matrix, fraction_to_str

def multiply_matrices(matA: Matrix, matB: Matrix):
    rowsA, colsA = matA.shape
    rowsB, colsB = matB.shape
    if colsA != rowsB:
        raise ValueError("Dimensiones incompatibles para multiplicación")
    result = [[sum(matA[i,k] * matB[k,j] for k in range(colsA)) for j in range(colsB)] for i in range(rowsA)]
    log = []
    log.append("OPERACIÓN: MULTIPLICACIÓN DE MATRICES")
    log.append(f"Dimensiones: A ({rowsA}×{colsA}) × B ({rowsB}×{colsB}) = Resultado ({rowsA}×{colsB})")
    for i in range(rowsA):
        for j in range(colsB):
            terms = []
            for k in range(colsA):
                terms.append(f"A[{i+1},{k+1}]×B[{k+1},{j+1}] = {fraction_to_str(matA[i,k])}×{fraction_to_str(matB[k,j])}")
            log.append(" + ".join(terms))
            log.append(f"C[{i+1},{j+1}] = {fraction_to_str(result[i][j])}")
    return Matrix(result), log
