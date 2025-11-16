"""Método de Falsa Posición (root finding) usando sympy/numpy para evaluación segura.

Este módulo crea un callable numérico a partir de la expresión de entrada utilizando
`sympy.parse_expr` + `lambdify` (módulo numpy). Maneja `^` como potencia, `pi`, `e`,
funciones matemáticas y multiplicación implícita.
"""

import math
import re
import warnings
from dataclasses import dataclass
from typing import Callable, Optional, List, Tuple

import numpy as np
from sympy import symbols, lambdify, pi, E
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application


Transformations = standard_transformations + (implicit_multiplication_application,)


def _build_callable(func_str: str) -> Callable[[float], float]:
    """Convierte una cadena en una función numérica f(x) usando sympy.

    Lanza ValueError si la expresión no puede parsearse o contiene símbolos no permitidos.
    """
    if not func_str or not func_str.strip():
        raise ValueError("Función vacía")

    s = func_str.strip()
    # Aceptar ^ como potencia
    s = s.replace('^', '**')
    # Normalizar uso de la constante 'e' para la base del logaritmo natural -> 'E'
    # Solo reemplazamos 'e' cuando aparece como token independiente (no parte de palabras)
    s = re.sub(r'(?<![A-Za-z0-9_])e(?![A-Za-z0-9_])', 'E', s)
    # Aceptar notación 'e^x' o 'e**x' si aparece sin paréntesis
    s = re.sub(r'E\*\*\(([^)]+)\)', r'exp(\1)', s)
    s = re.sub(r'E\*\*([A-Za-z0-9_]+)', r'exp(\1)', s)

    try:
        expr = parse_expr(s, transformations=Transformations)
    except Exception as e:
        raise ValueError(f"No se pudo parsear la función: {e}")

    # Crear lambda numérica basada en numpy
    try:
        x = symbols('x')
        f_num = lambdify(x, expr, modules=["numpy", {"pi": np.pi, "E": np.e}])
    except Exception as e:
        raise ValueError(f"No se pudo crear función numérica: {e}")

    def safe_f(x_val):
        try:
            y = f_num(x_val)
            # Manejar distintos tipos devueltos por lambdify/sympy/numpy
            # numpy arrays
            if isinstance(y, np.ndarray):
                # extraer escalar
                try:
                    return float(y.item())
                except Exception:
                    return float(np.asarray(y, dtype=float).ravel()[0])

            # numpy scalar
            if isinstance(y, (np.floating, np.integer)):
                return float(y)

            # Python numeric
            if isinstance(y, (int, float)):
                return float(y)

            # Sympy number or other object: intentar convertir con float(sympy.N(y))
            try:
                import sympy as _sym
                if isinstance(y, _sym.Basic):
                    return float(_sym.N(y))
            except Exception:
                pass

            # Fallback intentar array->float
            try:
                arr = np.asarray(y, dtype=float)
                return float(arr.ravel()[0])
            except Exception:
                raise ValueError(f"No se pudo convertir el resultado a float: {y}")

        except Exception as e:
            raise ValueError(f"Evaluación fallida en x={x_val}: {e}")

    return safe_f


def false_position_method(func_str: str, a: float, b: float, tol: float = 1e-4, max_iter: int = 100) -> Tuple[float, List[str], int]:
    """Calcula la raíz por el método de Falsa Posición.

    Devuelve (root, logs, iterations). Lanza ValueError con un mensaje claro si algo falla.
    """
    f = _build_callable(func_str)

    try:
        fa = f(a)
        fb = f(b)
    except Exception as e:
        raise ValueError(f"No se pudieron evaluar los extremos del intervalo: {e}")

    if math.isnan(fa) or math.isnan(fb):
        raise ValueError("No se pudieron evaluar puntos válidos en el intervalo.")

    if fa * fb > 0:
        raise ValueError("La función no cambia de signo en [a,b]")

    logs: List[str] = []
    iteration = 0
    prev_c: Optional[float] = None

    while iteration < max_iter:
        try:
            fa = f(a)
            fb = f(b)
        except Exception as e:
            raise ValueError(f"Evaluación fallida durante iteraciones: {e}")

        if fb == fa:
            logs.append("f(a) == f(b); fórmula indeterminada")
            break

        c = b - fb * (b - a) / (fb - fa)

        try:
            fc = f(c)
        except Exception as e:
            raise ValueError(f"No se pudo evaluar f(c) en c={c}: {e}")

        logs.append(f"Iter {iteration+1}: a={a}, b={b}, c={c}, f(c)={fc}")

        if abs(fc) <= tol or (prev_c is not None and abs(c - prev_c) <= tol):
            prev_c = c
            break

        if fa * fc < 0:
            b = c
        else:
            a = c

        prev_c = c
        iteration += 1

    root = prev_c if prev_c is not None else (a + b) / 2
    return root, logs, iteration

