import re
import math
import ast
import numpy as np
from fractions import Fraction
from matrix_core import fraction_to_str


def preprocess_function(func_str: str) -> str:
    s = func_str.strip()
    if not s:
        return s

    s = s.replace(" ", "")
    s = re.sub(r'e\*\*\(([^)]+)\)', r'exp(\1)', s)
    s = re.sub(r'e\*\*([a-zA-Z0-9_]+)', r'exp(\1)', s)
    s = re.sub(r'e\^\(([^)]+)\)', r'exp(\1)', s)
    s = re.sub(r'e\^([a-zA-Z0-9_]+)', r'exp(\1)', s)
    s = s.replace('^', '**')
    s = re.sub(r'([+\-])\*\*(\d+)', r'\1x**\2', s)
    s = re.sub(r'(\d+)([a-zA-Z(])', r'\1*\2', s)
    s = re.sub(r'\)([a-zA-Z(])', r')*\1', s)
    # Evitar insertar multiplicación entre nombres de función y '('
    # La multiplicación implícita ya está cubierta para dígitos con '(' y letras con dígitos.
    s = re.sub(r'\bsen([a-zA-Z])', r'sin\1', s)
    s = re.sub(r'\bsen\b', 'sin', s)
    s = re.sub(r'\bln([a-zA-Z])', r'log\1', s)
    s = re.sub(r'\bln\b', 'log', s)
    for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
        s = re.sub(rf'([a-zA-Z]){name}([a-zA-Z])', rf'\1*{name}(\2)', s)
    # Wrap missing parentheses: sinx -> sin(x), cosx -> cos(x), etc. Avoid log10.
    s = re.sub(r'\b(?!log10)(sin|cos|tan|exp|log|sqrt)(?!\()([A-Za-z0-9_.]+)', r'\1(\2)', s)
    for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
        s = re.sub(rf'\b{name}\s*(?=\()', f'math.{name}', s)
    s = re.sub(r'\blog10\s*(?=\()', 'math.log10', s)
    s = re.sub(r'π', 'math.pi', s)
    s = re.sub(r'(?<!\w)pi(?!\w)', 'math.pi', s)
    s = re.sub(r'(?<!\w)(?<!math\.)(?<!exp\()e(?!\w)(?!xp)', 'math.e', s)
    s = re.sub(r'math\.e\*\*(\([^()]*\)|[A-Za-z0-9_.]+)', r'math.exp(\1)', s)
    return s


def evaluate_function(x, func_str: str) -> float:
    try:
        s = func_str.strip()
        if not s:
            raise ValueError("Función vacía")

        original_func = s
        s = preprocess_function(s)
        s = re.sub(r'(?<=\d)(?=x|\()', '*', s)
        s = re.sub(r'(?<=x)(?=\d|\()', '*', s)
        s = re.sub(r'(?<=\))(?=[\dx(])', '*', s)
        s = re.sub(r'(?<=math\.pi)(?=[\dx(])', '*', s)
        s = re.sub(r'(?<=math\.e)(?=(?:[\d(]|x(?!p)))', '*', s)

        # AST validation
        try:
            tree = ast.parse(s, mode='eval')
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id not in ['x', 'math', 'abs']:
                    raise ValueError(f"Variable no permitida: {node.id}")
                elif isinstance(node, ast.Attribute) and node.attr not in ['sin', 'cos', 'tan', 'exp', 'log', 'log10', 'pi', 'e', 'sqrt']:
                    raise ValueError(f"Función no permitida: {node.attr}")
        except SyntaxError:
            raise ValueError(f"Sintaxis inválida en la función: {original_func}")

        env = {"x": x, "math": math, "abs": abs}
        try:
            result = eval(s, {"__builtins__": {}}, env)
        except Exception as e:
            msg = str(e)
            if 'math domain error' in msg:
                hints = []
                if re.search(r'\bln\b|\blog\b', original_func):
                    hints.append('ln(x)/log(x) requiere x>0')
                if 'sqrt' in original_func:
                    hints.append('sqrt(...) requiere argumento \u2265 0')
                hint_msg = (': ' + '; '.join(hints)) if hints else ''
                raise ValueError(f'Dominio inválido al evaluar f(x){hint_msg}. Ajusta el intervalo. x={x}')
            raise ValueError(msg)
        if not isinstance(result, (int, float)):
            raise ValueError("La función debe devolver un número")
        return float(result)
    except Exception as e:
        raise ValueError(str(e))


def evaluate_function_vectorized(x_array, func_str: str):
    try:
        s = func_str.strip()
        if not s:
            raise ValueError("Función vacía")
        s = preprocess_function(s)
        s = s.replace("math.sin", "np.sin")
        s = s.replace("math.cos", "np.cos")
        s = s.replace("math.tan", "np.tan")
        s = s.replace("math.exp", "np.exp")
        s = s.replace("math.log", "np.log")
        s = s.replace("math.log10", "np.log10")
        s = s.replace("math.sqrt", "np.sqrt")
        s = s.replace("abs(", "np.abs(")
        s = s.replace("math.pi", "np.pi")
        s = s.replace("math.e", "np.e")
        env = {"x": x_array, "np": np, "math": math, "abs": np.abs}
        with np.errstate(all='ignore'):
            result = eval(s, {"__builtins__": {}}, env)
        result = np.array(result, dtype=float)
        result = np.where(np.isinf(result), np.nan, result)
        return result
    except Exception as e:
        raise ValueError(str(e))


def format_function_display(func_str: str) -> str:
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '+': '⁺', '-': '⁻', '(': '⁽', ')': '⁾',
        'x': 'ˣ', 'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ',
        'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ', 'i': 'ⁱ',
        'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ',
        'o': 'ᵒ', 'p': 'ᵖ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ',
        'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'y': 'ʸ', 'z': 'ᶻ'
    }

    def to_superscript(text):
        return ''.join(superscript_map.get(char, char) for char in text)

    result = func_str
    result = re.sub(r'\bpi\b', 'π', result)
    result = re.sub(r'\bexp\(([^)]+)\)', r'e^(\1)', result)

    def replace_power(match):
        base = match.group(1)
        exponent = match.group(2)
        if len(exponent) == 1:
            return base + to_superscript(exponent)
        else:
            converted = ''
            for char in exponent:
                converted += superscript_map.get(char, char)
            return base + converted

    def replace_power_with_paren(match):
        base = match.group(1)
        exponent_content = match.group(2)
        converted = ''
        for char in exponent_content:
            converted += superscript_map.get(char, char)
        return base + converted

    result = re.sub(r'([a-zA-Z0-9πe]+)\^\(([^)]+)\)', replace_power_with_paren, result)
    result = re.sub(r'([a-zA-Z0-9πe]+)\^([a-zA-Z0-9]+)', replace_power, result)
    def replace_power_unary_minus(match):
        base = match.group(1)
        sym = match.group(2)
        converted = superscript_map['-'] + superscript_map.get(sym, sym)
        return base + converted
    result = re.sub(r'([a-zA-Z0-9πe]+)\^-([a-zA-Z0-9])', replace_power_unary_minus, result)
    return result
