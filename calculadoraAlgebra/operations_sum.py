from matrix_core import Matrix, fraction_to_str, format_matrix_lines

def add_matrices(matA: Matrix, matB: Matrix):
    """Devuelve (result_matrix, log_lines) donde log_lines es lista de strings."""
    if matA.shape != matB.shape:
        raise ValueError("Dimensiones no coinciden")
    rows, cols = matA.shape
    result = []
    log = [
        f"Paso 1: Verificar dimensiones compatibles A({rows}×{cols}) y B({rows}×{cols})",
        "Paso 2: Sumar elemento a elemento",
    ]
    for i in range(rows):
        row = []
        for j in range(cols):
            a_val = matA[i, j]
            b_val = matB[i, j]
            s = a_val + b_val
            row.append(s)
            log.append(
                f"  Paso 2.{i+1}.{j+1}: C[{i+1},{j+1}] = {fraction_to_str(a_val)} + {fraction_to_str(b_val)} = {fraction_to_str(s)}"
            )
        result.append(row)
    res_matrix = Matrix(result)
    log.append("Paso final: Matriz resultado C =")
    log.extend(format_matrix_lines(res_matrix))
    return res_matrix, log
