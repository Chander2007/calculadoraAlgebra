from matrix_core import Matrix, fraction_to_str

def add_matrices(matA: Matrix, matB: Matrix):
    """Devuelve (result_matrix, log_lines) donde log_lines es lista de strings."""
    if matA.shape != matB.shape:
        raise ValueError("Dimensiones no coinciden")
    rows, cols = matA.shape
    result = [[matA[i,j] + matB[i,j] for j in range(cols)] for i in range(rows)]
    log = []
    log.append("OPERACIÓN: SUMA DE MATRICES")
    for i in range(rows):
        for j in range(cols):
            a_val = matA[i,j]
            b_val = matB[i,j]
            s = result[i][j]
            log.append(f"C[{i+1},{j+1}] = A[{i+1},{j+1}] + B[{i+1},{j+1}] = {fraction_to_str(a_val)} + {fraction_to_str(b_val)} = {fraction_to_str(s)}")
    return Matrix(result), log
