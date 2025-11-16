from fractions import Fraction
from matrix_core import Matrix

def gauss_jordan_solve(matrix):
    """Recibe matriz aumentada (list of lists of Fraction). Devuelve (status, result_or_log)
    status: 'unique', 'infinite', 'inconsistent'
    result_or_log: if unique -> solution list; if others -> log lines list
    """
    mat = [row[:] for row in matrix]
    rows = len(mat)
    cols = len(mat[0])
    n_vars = cols - 1
    pivot_cols = []
    log = []
    # eliminación
    r = 0
    for c in range(n_vars):
        # buscar pivote
        piv = None
        for i in range(r, rows):
            if mat[i][c] != 0:
                piv = i
                break
        if piv is None:
            continue
        if piv != r:
            mat[r], mat[piv] = mat[piv], mat[r]
            log.append(f"Intercambiar fila {r+1} con {piv+1}")
        # normalizar
        pivot = mat[r][c]
        for j in range(c, cols):
            mat[r][j] = mat[r][j] / pivot
        log.append(f"Dividir fila {r+1} por {pivot}")
        # eliminar
        for i in range(rows):
            if i!=r and mat[i][c] != 0:
                factor = mat[i][c]
                for j in range(c, cols):
                    mat[i][j] -= factor * mat[r][j]
                log.append(f"R{i+1} = R{i+1} - {factor} * R{r+1}")
        pivot_cols.append(c)
        r += 1
        if r==rows:
            break

    # comprobar inconsistencia
    for i in range(rows):
        if all(mat[i][j]==0 for j in range(n_vars)) and mat[i][-1] != 0:
            log.append("Sistema inconsistente")
            return 'inconsistent', log

    if len(pivot_cols) < n_vars:
        # infinitas soluciones
        log.append("Sistema con infinitas soluciones (variables libres)")
        return 'infinite', log

    # solución única
    sol = [mat[i][-1] for i in range(n_vars)]
    return 'unique', sol
