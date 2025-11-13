from matrix_core import _determinant_step, _determinant_sarrus, fraction_to_str, Matrix

def determinant_with_log(matrix):
    """matrix: list of lists of Fraction; returns (det, log_lines)"""
    n = len(matrix)
    log = []
    if n == 3:
        log.append("Usando regla de Sarrus para 3x3")
        # show matrix content
        for row in matrix:
            log.append(" ".join(fraction_to_str(x) for x in row))
        det = _determinant_sarrus(matrix)
        log.append(f"determinante = {fraction_to_str(det)}")
        return det, log
    else:
        log.append("Usando reducción por filas")
        for row in matrix:
            log.append(" ".join(fraction_to_str(x) for x in row))
        det = _determinant_step(matrix)
        log.append(f"determinante = {fraction_to_str(det)}")
        return det, log
