from matrix_core import Matrix, fraction_to_str, format_matrix_lines
from operations_determinant import determinant_with_log

def cofactor_matrix(matA: Matrix):
    if matA.rows != matA.cols:
        raise ValueError("La matriz debe ser cuadrada para cofactores")
    n = matA.rows
    log = [
        "Paso 1: Confirmar matriz cuadrada para calcular cofactores",
        "Paso 2: Registrar matriz original A",
        *format_matrix_lines(matA),
    ]
    cofact = []
    for i in range(n):
        row = []
        for j in range(n):
            log.append(f"Paso 3.{i+1}.{j+1}: Construir menor eliminando fila {i+1} y columna {j+1}")
            sub = [[matA[r, c] for c in range(n) if c != j] for r in range(n) if r != i]
            log.extend(f"    {line}" for line in format_matrix_lines(sub))
            det_sub, det_log = determinant_with_log(sub)
            log.append(f"    Resultado del determinante del menor:")
            log.extend(f"      {line}" for line in det_log)
            sign = (-1) ** (i + j)
            cof = sign * det_sub
            row.append(cof)
            log.append(
                f"    Cofactor C[{i+1},{j+1}] = (-1)^({i+1}+{j+1}) × {fraction_to_str(det_sub)} = {fraction_to_str(cof)}"
            )
        cofact.append(row)
    result_matrix = Matrix(cofact)
    log.append("Paso final: Matriz de cofactores C =")
    log.extend(format_matrix_lines(result_matrix))
    return result_matrix, log
