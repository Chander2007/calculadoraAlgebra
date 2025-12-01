from fractions import Fraction
from matrix_core import _determinant_step, _determinant_sarrus, fraction_to_str, Matrix, format_matrix_lines

def determinant_with_log(matrix):
    data = matrix.data if isinstance(matrix, Matrix) else matrix
    n = len(data)
    log = ["Paso 1: Registrar matriz para determinar |A|", *format_matrix_lines(data)]
    if n == 3:
        log.append("Paso 2: Aplicar regla de Sarrus")
        main_positions = [
            ((0, 0), (1, 1), (2, 2)),
            ((0, 1), (1, 2), (2, 0)),
            ((0, 2), (1, 0), (2, 1)),
        ]
        main_sum = Fraction(0)
        for idx, positions in enumerate(main_positions, start=1):
            vals = [data[r][c] for r, c in positions]
            prod = vals[0] * vals[1] * vals[2]
            indices_txt = " × ".join(f"A[{r+1},{c+1}]" for r, c in positions)
            values_txt = " × ".join(fraction_to_str(v) for v in vals)
            log.append(
                f"  Paso 2.{idx}: {indices_txt} = {values_txt} = {fraction_to_str(prod)}"
            )
            main_sum += prod
        log.append(f"  Suma diagonales principales = {fraction_to_str(main_sum)}")
        secondary_positions = [
            ((0, 2), (1, 1), (2, 0)),
            ((0, 0), (1, 2), (2, 1)),
            ((0, 1), (1, 0), (2, 2)),
        ]
        secondary_sum = Fraction(0)
        log.append("Paso 3: Restar diagonales secundarias")
        for idx, positions in enumerate(secondary_positions, start=1):
            vals = [data[r][c] for r, c in positions]
            prod = vals[0] * vals[1] * vals[2]
            indices_txt = " × ".join(f"A[{r+1},{c+1}]" for r, c in positions)
            values_txt = " × ".join(fraction_to_str(v) for v in vals)
            log.append(
                f"  Paso 3.{idx}: {indices_txt} = {values_txt} = {fraction_to_str(prod)}"
            )
            secondary_sum += prod
        log.append(f"  Suma diagonales secundarias = {fraction_to_str(secondary_sum)}")
        det = main_sum - secondary_sum
        log.append(
            f"Paso 4: Determinante = {fraction_to_str(main_sum)} - {fraction_to_str(secondary_sum)} = {fraction_to_str(det)}"
        )
    else:
        log.append("Paso 2: Aplicar eliminación por filas (Gauss) para obtener determinante")
        det = _determinant_step(data)
        log.append(f"Paso 3: Determinante calculado = {fraction_to_str(det)}")
    log.append("Paso final: Representar determinante como matriz 1×1")
    log.extend(format_matrix_lines([[det]]))
    return det, log
