from math_utils import evaluate_function
import math

def bisection_method(func_str, a, b, tol=1e-4, max_iter=100):
    logs = []
    fa = evaluate_function(a, func_str)
    fb = evaluate_function(b, func_str)
    if fa * fb > 0:
        raise ValueError("La función no cambia de signo en [a,b]")
    iteration = 0
    prev_c = None
    while (b - a)/2 > tol and iteration < max_iter:
        c = (a + b)/2
        fc = evaluate_function(c, func_str)
        logs.append(f"Iter {iteration+1}: a={a}, b={b}, c={c}, f(c)={fc}")
        if abs(fc) <= tol:
            prev_c = c
            break
        if fa * fc < 0:
            b = c
            fb = fc
        else:
            a = c
            fa = fc
        prev_c = c
        iteration += 1
    root = prev_c if prev_c is not None else (a + b)/2
    return root, logs, iteration
