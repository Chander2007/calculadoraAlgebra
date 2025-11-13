from matrix_core import Matrix, fraction_to_str
from operations_determinant import determinant_with_log

def cofactor_matrix(matA: Matrix):
    if matA.rows != matA.cols:
        raise ValueError("La matriz debe ser cuadrada para cofactores")
    n = matA.rows
    cofact = []
    log = []
    for i in range(n):
        row = []
        for j in range(n):
            sub = [[matA[r,c] for c in range(n) if c!=j] for r in range(n) if r!=i]
            det_sub, det_log = determinant_with_log(sub)
            sign = (-1)**(i+j)
            cof = sign * det_sub
            row.append(cof)
            log.append(f"C[{i+1},{j+1}] = {fraction_to_str(cof)}")
        cofact.append(row)
    return Matrix(cofact), log
