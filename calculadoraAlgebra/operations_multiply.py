from matrix_core import Matrix, fraction_to_str, format_matrix_lines

def multiply_matrices(matA: Matrix, matB: Matrix):
    rowsA, colsA = matA.shape
    rowsB, colsB = matB.shape
    if colsA != rowsB:
        raise ValueError("Dimensiones incompatibles para multiplicación")
    log = [
        f"Paso 1: Verificar dimensiones A({rowsA}×{colsA}) y B({rowsB}×{colsB}) → columnas de A igual a filas de B",
        "Paso 2: Calcular cada entrada C[i,j] como producto fila-columna",
    ]
    result = []
    for i in range(rowsA):
        row = []
        for j in range(colsB):
            partial_products = []
            for k in range(colsA):
                a_val = matA[i, k]
                b_val = matB[k, j]
                prod = a_val * b_val
                partial_products.append(prod)
                log.append(
                    f"  Paso 2.{i+1}.{j+1}.{k+1}: A[{i+1},{k+1}] × B[{k+1},{j+1}] = {fraction_to_str(a_val)} × {fraction_to_str(b_val)} = {fraction_to_str(prod)}"
                )
            cell_value = sum(partial_products)
            terms = " + ".join(fraction_to_str(val) for val in partial_products)
            log.append(
                f"  Paso 2.{i+1}.{j+1}: C[{i+1},{j+1}] = {terms} = {fraction_to_str(cell_value)}"
            )
            row.append(cell_value)
        result.append(row)
    res_matrix = Matrix(result)
    log.append("Paso final: Matriz resultado C =")
    log.extend(format_matrix_lines(res_matrix))
    return res_matrix, log
