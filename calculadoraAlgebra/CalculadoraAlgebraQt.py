from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit, QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QAbstractScrollArea, QScrollArea, QSlider, QSizePolicy, QButtonGroup
from PySide6.QtCore import Qt
from fractions import Fraction
import numpy as np
import math
import re
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matrix_core import Matrix, fraction_to_str
import operations_sum, operations_subtract, operations_multiply, operations_determinant, operations_cofactor, operations_gauss, root_bisection, root_falsepos, math_utils

def parse_fraction(text: str) -> Fraction:
    s = text.strip()
    if not s:
        return Fraction(0)
    if "/" in s:
        num, den = s.split("/", 1)
        return Fraction(int(num.strip()), int(den.strip()))
    try:
        if s.lower() in ("pi", "π"):
            return Fraction.from_float(math.pi)
        if s.lower() == "e":
            return Fraction.from_float(math.e)
        if any(ch in s for ch in ".eE"):
            return Fraction.from_float(float(s))
        return Fraction(int(s))
    except Exception:
        return Fraction.from_float(float(s))

class MatricesPage(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.rows = 3
        self.colsA = 3
        self.colsB = 3
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel("Operaciones con Matrices")
        title.setStyleSheet(f"color:{colors['accent']};")
        title.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignLeft)
        top = QHBoxLayout()
        layout.addLayout(top)
        self.operation = QComboBox()
        self.operation.addItems(["Suma", "Resta", "Multiplicación", "Determinante", "Cofactor"])
        self.operation.setFixedWidth(220)
        top.addWidget(QLabel("Operación:"), alignment=Qt.AlignLeft)
        top.addWidget(self.operation, alignment=Qt.AlignLeft)
        dim = QHBoxLayout()
        self.spin_rows = QSpinBox(); self.spin_rows.setRange(1, 10); self.spin_rows.setValue(3)
        self.spin_colsA = QSpinBox(); self.spin_colsA.setRange(1, 10); self.spin_colsA.setValue(3)
        self.spin_colsB = QSpinBox(); self.spin_colsB.setRange(1, 10); self.spin_colsB.setValue(3)
        dim.addWidget(QLabel("Filas (A):")); dim.addWidget(self.spin_rows)
        dim.addWidget(QLabel("Cols A:")); dim.addWidget(self.spin_colsA)
        dim.addWidget(QLabel("Cols B:")); dim.addWidget(self.spin_colsB)
        top.addLayout(dim)
        self.view_mode = QComboBox(); self.view_mode.addItems(["Apilada", "Lado a lado"])
        top.addWidget(QLabel("Vista:")); top.addWidget(self.view_mode)
        btns = QHBoxLayout()
        self.btn_generate = QPushButton("Generar")
        self.btn_solve = QPushButton("Resolver")
        self.btn_clear = QPushButton("Limpiar")
        btns.addStretch(1)
        for b in (self.btn_generate, self.btn_solve, self.btn_clear):
            b.setMinimumWidth(140)
            btns.addWidget(b)
        layout.addLayout(btns)
        self.body = QVBoxLayout()
        layout.addLayout(self.body)
        self.view_mode.currentTextChanged.connect(lambda _: self.build_body(self.view_mode.currentText()=="Apilada"))
        self.build_body(True)
        self.btn_generate.clicked.connect(lambda: (self.generate_tables(), self._auto_resize_table(self.tableA), self._auto_resize_table(self.tableB)))
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_solve.clicked.connect(self.solve_operation)
        self.apply_palette()

    def apply_palette(self):
        self.setStyleSheet(f"""
            QTableWidget {{ background-color: {self.colors['matrix_bg']}; color: {self.colors['text']}; gridline-color: {self.colors['secondary_bg']}; selection-background-color: {self.colors['accent']}; }}
            QHeaderView::section {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; padding:6px; border:0px; }}
            QLabel {{ color:{self.colors['text']}; }}
            QPlainTextEdit {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; border:1px solid {self.colors['secondary_bg']}; }}
        """)

    def build_body(self, stacked: bool):
        self._clear_layout(self.body)
        self.tableA = QTableWidget(3, 3)
        self.tableB = QTableWidget(3, 3)
        for t in (self.tableA, self.tableB):
            t.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            t.verticalHeader().setVisible(False)
        sectionA = QVBoxLayout(); sectionA.addWidget(QLabel("Matriz A")); sectionA.addWidget(self.tableA)
        controlsA = QHBoxLayout()
        btn_a_sub_row = QPushButton("− Fila"); btn_a_add_row = QPushButton("+ Fila")
        btn_a_sub_col = QPushButton("− Col"); btn_a_add_col = QPushButton("+ Col")
        for b in (btn_a_sub_row, btn_a_add_row, btn_a_sub_col, btn_a_add_col): b.setMinimumWidth(100)
        controlsA.addWidget(btn_a_sub_row); controlsA.addWidget(btn_a_add_row); controlsA.addWidget(btn_a_sub_col); controlsA.addWidget(btn_a_add_col)
        sectionA.addLayout(controlsA)
        sectionB = QVBoxLayout(); sectionB.addWidget(QLabel("Matriz B")); sectionB.addWidget(self.tableB)
        controlsB = QHBoxLayout()
        btn_b_sub_row = QPushButton("− Fila"); btn_b_add_row = QPushButton("+ Fila")
        btn_b_sub_col = QPushButton("− Col"); btn_b_add_col = QPushButton("+ Col")
        for b in (btn_b_sub_row, btn_b_add_row, btn_b_sub_col, btn_b_add_col): b.setMinimumWidth(100)
        controlsB.addWidget(btn_b_sub_row); controlsB.addWidget(btn_b_add_row); controlsB.addWidget(btn_b_sub_col); controlsB.addWidget(btn_b_add_col)
        sectionB.addLayout(controlsB)
        if stacked:
            self.body.addLayout(sectionA)
            self.body.addLayout(sectionB)
        else:
            split = QHBoxLayout(); split.addLayout(sectionA,1); split.addLayout(sectionB,1)
            self.body.addLayout(split)
        result_box = QVBoxLayout()
        self.result_table = QTableWidget(0, 0)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        result_box.addWidget(QLabel("Resultado")); result_box.addWidget(self.result_table)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(160)
        result_box.addWidget(QLabel("Detalle")); result_box.addWidget(self.log, 1)
        self.body.addLayout(result_box)
        self._auto_resize_table(self.tableA); self._auto_resize_table(self.tableB)
        btn_a_add_row.clicked.connect(lambda: (self._add_row(self.tableA), self._auto_resize_table(self.tableA)))
        btn_a_sub_row.clicked.connect(lambda: (self._sub_row(self.tableA), self._auto_resize_table(self.tableA)))
        btn_a_add_col.clicked.connect(lambda: (self._add_col(self.tableA), self._auto_resize_table(self.tableA)))
        btn_a_sub_col.clicked.connect(lambda: (self._sub_col(self.tableA), self._auto_resize_table(self.tableA)))
        btn_b_add_row.clicked.connect(lambda: (self._add_row(self.tableB), self._auto_resize_table(self.tableB)))
        btn_b_sub_row.clicked.connect(lambda: (self._sub_row(self.tableB), self._auto_resize_table(self.tableB)))
        btn_b_add_col.clicked.connect(lambda: (self._add_col(self.tableB), self._auto_resize_table(self.tableB)))
        btn_b_sub_col.clicked.connect(lambda: (self._sub_col(self.tableB), self._auto_resize_table(self.tableB)))

    def generate_tables(self):
        self.rows = self.spin_rows.value()
        self.colsA = self.spin_colsA.value()
        self.colsB = self.spin_colsB.value()
        self.tableA.setRowCount(self.rows); self.tableA.setColumnCount(self.colsA)
        self.tableB.setRowCount(self.rows); self.tableB.setColumnCount(self.colsB)
        for c in range(self.colsA):
            self.tableA.setColumnWidth(c, 100)
        for c in range(self.colsB):
            self.tableB.setColumnWidth(c, 100)
        for r in range(self.rows):
            for c in range(self.colsA):
                self.tableA.setItem(r, c, QTableWidgetItem("0"))
        for r in range(self.rows):
            for c in range(self.colsB):
                self.tableB.setItem(r, c, QTableWidgetItem("0"))

    def read_matrix(self, table) -> Matrix:
        rows = table.rowCount(); cols = table.columnCount(); data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                item = table.item(r, c); text = item.text() if item else "0"
                row.append(parse_fraction(text))
            data.append(row)
        return Matrix(data)

    def set_result_matrix(self, mat: Matrix):
        self.result_table.setRowCount(mat.rows); self.result_table.setColumnCount(mat.cols)
        for r in range(mat.rows):
            for c in range(mat.cols):
                self.result_table.setItem(r, c, QTableWidgetItem(fraction_to_str(mat[r, c])))

    def solve_operation(self):
        op = self.operation.currentText()
        self.log.clear()
        try:
            if op in ("Suma", "Resta", "Multiplicación"):
                matA = self.read_matrix(self.tableA); matB = self.read_matrix(self.tableB)
                if op == "Suma":
                    res, logs = operations_sum.add_matrices(matA, matB)
                elif op == "Resta":
                    res, logs = operations_subtract.subtract_matrices(matA, matB)
                else:
                    res, logs = operations_multiply.multiply_matrices(matA, matB)
                self.set_result_matrix(res); self.log.appendPlainText("\n".join(logs))
            elif op == "Determinante":
                matA = self.read_matrix(self.tableA)
                det, logs = operations_determinant.determinant_with_log(matA.data)
                self.result_table.setRowCount(1); self.result_table.setColumnCount(1)
                self.result_table.setItem(0, 0, QTableWidgetItem(fraction_to_str(det)))
                self.log.appendPlainText("\n".join(logs))
            elif op == "Cofactor":
                matA = self.read_matrix(self.tableA)
                res, logs = operations_cofactor.cofactor_matrix(matA)
                self.set_result_matrix(res); self.log.appendPlainText("\n".join(logs))
        except Exception as e:
            self.log.appendPlainText(f"Error: {e}")

    def clear_all(self):
        for tbl in (self.tableA, self.tableB, self.result_table):
            tbl.clear(); tbl.setRowCount(0); tbl.setColumnCount(0)
        self.log.clear()

    def _add_row(self, table: QTableWidget):
        r = table.rowCount(); table.insertRow(r)
        for c in range(table.columnCount()):
            table.setItem(r, c, QTableWidgetItem("0"))

    def _sub_row(self, table: QTableWidget):
        r = table.rowCount()
        if r>0:
            table.removeRow(r-1)

    def _add_col(self, table: QTableWidget):
        c = table.columnCount(); table.insertColumn(c)
        for r in range(table.rowCount()):
            table.setItem(r, c, QTableWidgetItem("0"))

    def _sub_col(self, table: QTableWidget):
        c = table.columnCount()
        if c>0:
            table.removeColumn(c-1)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            else:
                sub = item.layout()
                if sub:
                    self._clear_layout(sub)

    def _auto_resize_table(self, table: QTableWidget):
        table.resizeRowsToContents()
        h = table.verticalHeader().length() + table.horizontalHeader().height() + 6
        table.setMinimumHeight(h)

class GaussJordanPage(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        layout = QVBoxLayout(self); layout.setContentsMargins(24,24,24,24); layout.setSpacing(16)
        title = QLabel("Método de Gauss‑Jordan")
        title.setStyleSheet(f"color:{colors['accent']};"); title.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignLeft)
        controls = QHBoxLayout()
        self.spin_rows = QSpinBox(); self.spin_rows.setRange(1, 10); self.spin_rows.setValue(3)
        self.spin_cols = QSpinBox(); self.spin_cols.setRange(1, 10); self.spin_cols.setValue(3)
        controls.addWidget(QLabel("Ecuaciones:")); controls.addWidget(self.spin_rows)
        controls.addWidget(QLabel("Variables:")); controls.addWidget(self.spin_cols)
        layout.addLayout(controls)
        self.btn_generate = QPushButton("Generar Matriz Aumentada")
        self.btn_solve = QPushButton("Resolver"); self.btn_clear = QPushButton("Limpiar")
        btns = QHBoxLayout(); btns.addStretch(1)
        for b in (self.btn_generate, self.btn_solve, self.btn_clear):
            b.setMinimumWidth(180); btns.addWidget(b)
        layout.addLayout(btns)
        self.table = QTableWidget(3, 4)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for c in range(self.table.columnCount()):
            self.table.setColumnWidth(c, 100)
        layout.addWidget(self.table)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(160)
        layout.addWidget(QLabel("Detalle")); layout.addWidget(self.log)
        self.btn_generate.clicked.connect(self.generate_matrix)
        self.btn_solve.clicked.connect(self.solve)
        self.btn_clear.clicked.connect(self.clear)
        self.setStyleSheet(f"QLabel {{ color:{self.colors['text']}; }} QTableWidget {{ background:{self.colors['matrix_bg']}; color:{self.colors['text']}; }} QPlainTextEdit {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; }}")

    def generate_matrix(self):
        rows = self.spin_rows.value(); cols = self.spin_cols.value()
        self.table.setRowCount(rows); self.table.setColumnCount(cols + 1)
        for c in range(self.table.columnCount()):
            self.table.setColumnWidth(c, 100)
        for r in range(rows):
            for c in range(cols + 1):
                self.table.setItem(r, c, QTableWidgetItem("0"))

    def solve(self):
        rows = self.table.rowCount(); cols = self.table.columnCount(); data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                item = self.table.item(r, c); text = item.text() if item else "0"
                row.append(parse_fraction(text))
            data.append(row)
        try:
            status, result = operations_gauss.gauss_jordan_solve(data)
            self.log.clear()
            if status == 'unique':
                self.log.appendPlainText("Solución única:")
                for i, val in enumerate(result, start=1):
                    self.log.appendPlainText(f"x{i} = {fraction_to_str(val)}")
            elif status == 'infinite':
                self.log.appendPlainText("Infinitas soluciones (variables libres)")
                self.log.appendPlainText("\n".join(result))
            else:
                self.log.appendPlainText("Sistema inconsistente")
                self.log.appendPlainText("\n".join(result))
        except Exception as e:
            self.log.appendPlainText(f"Error: {e}")

    def clear(self):
        self.table.clear(); self.table.setRowCount(0); self.table.setColumnCount(0)
        self.log.clear()

class RootFindingPage(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.current_method = "Bisección"
        self.last_root = None
        self.last_func = ""
        self.last_params = {}
        main = QVBoxLayout(self); main.setContentsMargins(24, 24, 24, 24); main.setSpacing(16)

        left = QVBoxLayout(); left.setSpacing(12)
        title = QLabel("Configuración")
        title.setStyleSheet(f"color:{self.colors['text']};")
        title.setFont(QtGui.QFont("Segoe UI", 18, QtGui.QFont.Bold))
        left.addWidget(title)

        self.func = QLineEdit(); self.func.setPlaceholderText("tan(x) - x")
        left.addWidget(self.func)

        method_bar = QHBoxLayout()
        self.btn_bis = QPushButton("Bisección")
        self.btn_fp = QPushButton("Falsa Posición")
        self.btn_newton = QPushButton("Newton-Raphson")
        self.btn_secant = QPushButton("Secante")
        self.method_buttons = {
            "Bisección": self.btn_bis,
            "Falsa Posición": self.btn_fp,
            "Newton-Raphson": self.btn_newton,
            "Secante": self.btn_secant,
        }
        for btn in self.method_buttons.values():
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(36)
            btn.setStyleSheet(f"background:{self.colors['secondary_bg']}; color:{self.colors['text']}; border-radius:6px; padding:8px 12px;")
            method_bar.addWidget(btn)
        left.addLayout(method_bar)

        grid = QGridLayout(); grid.setHorizontalSpacing(10); grid.setVerticalSpacing(6)
        for text in ("a / x₀:", "b / x₁:", "Tolerancia:", "Máx. iteraciones:"):
            lbl = QLabel(text); lbl.setStyleSheet(f"color:{self.colors['text']};"); grid.addWidget(lbl, *(divmod(list(("a / x₀:", "b / x₁:", "Tolerancia:", "Máx. iteraciones:")).index(text), 2)))
        self.a = QDoubleSpinBox(); self.a.setRange(-1e6, 1e6); self.a.setDecimals(8); self.a.setValue(-1.0)
        self.b = QDoubleSpinBox(); self.b.setRange(-1e6, 1e6); self.b.setDecimals(8); self.b.setValue(1.0)
        self.tol = QDoubleSpinBox(); self.tol.setRange(1e-12, 1.0); self.tol.setDecimals(10); self.tol.setValue(1e-4)
        self.max_iter = QSpinBox(); self.max_iter.setRange(1, 10000); self.max_iter.setValue(100)
        grid.addWidget(self.a, 0, 1); grid.addWidget(self.b, 0, 3); grid.addWidget(self.tol, 1, 1); grid.addWidget(self.max_iter, 1, 3)
        left.addLayout(grid)

        actions = QHBoxLayout()
        self.btn_calc = QPushButton("Calcular")
        self.btn_plot = QPushButton("Graficar")
        self.btn_suggest = QPushButton("Sugerir intervalo")
        self.btn_clear = QPushButton("Limpiar")
        for btn in (self.btn_calc, self.btn_plot, self.btn_suggest, self.btn_clear):
            btn.setCursor(Qt.PointingHandCursor)
            actions.addWidget(btn)
        left.addLayout(actions)

        keypad = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"), ("ln(x)", "ln(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x^2"), ("x³", "x^3"), ("1/x", "1/x"), ("x", "x"), ("π", "pi"), ("e", "e"),
            ("|x|", "abs(x)"), ("+", "+"), ("-", "-"), ("×", "*"), ("÷", "/"), ("(", "("),
            (")", ")"), ("^", "^"), ("Borrar", "<DEL>")
        ]
        grid_keys = QGridLayout(); grid_keys.setHorizontalSpacing(12); grid_keys.setVerticalSpacing(10)
        for idx, (text, value) in enumerate(keypad):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(32)
            btn.setStyleSheet(f"background:{self.colors['secondary_bg']}; color:{self.colors['text']}; border-radius:6px; padding:6px 10px;")
            btn.clicked.connect(lambda _, v=value: self.insert_text(v))
            grid_keys.addWidget(btn, idx // 6, idx % 6)
        left.addLayout(grid_keys)

        right = QVBoxLayout(); right.setSpacing(10)
        lbl_prev = QLabel("Previsualización:"); lbl_prev.setStyleSheet(f"color:{self.colors['text']};")
        right.addWidget(lbl_prev)
        self.preview_fig = Figure(figsize=(3, 0.6), dpi=150)
        self.preview_ax = self.preview_fig.add_subplot(111); self.preview_ax.axis("off")
        self.preview_canvas = FigureCanvasQTAgg(self.preview_fig); self.preview_canvas.setFixedHeight(60)
        right.addWidget(self.preview_canvas)

        self.figure = Figure(figsize=(7.2, 5.0), dpi=150)
        self.plot_ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure); self.canvas.setMinimumHeight(420)
        self.toolbar = NavigationToolbar2QT(self.canvas)
        right.addWidget(self.toolbar); right.addWidget(self.canvas)

        bottom = QVBoxLayout()
        lbl_res = QLabel("Resultados"); lbl_res.setStyleSheet(f"color:{self.colors['text']};")
        bottom.addWidget(lbl_res)
        controls_res = QHBoxLayout(); controls_res.addStretch(1)
        controls_res.addWidget(QLabel("Tamaño texto:", parent=self)); self.slider_font = QSlider(Qt.Horizontal)
        self.slider_font.setRange(8, 16); self.slider_font.setValue(10)
        controls_res.addWidget(self.slider_font); bottom.addLayout(controls_res)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(220); self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log.setFont(QtGui.QFont("Consolas", 10)); bottom.addWidget(self.log)

        left_widget = QWidget(); left_widget.setLayout(left)
        left_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        layout_top = QHBoxLayout(); layout_top.setContentsMargins(0, 0, 0, 0)
        layout_top.addWidget(left_widget)
        layout_top.addLayout(right)
        layout_top.setStretch(0, 5)
        layout_top.setStretch(1, 7)
        main.addLayout(layout_top); main.addLayout(bottom)
        main.setStretch(0, 3); main.setStretch(1, 1)

        self.btn_bis.clicked.connect(lambda: self._set_method("Bisección"))
        self.btn_fp.clicked.connect(lambda: self._set_method("Falsa Posición"))
        self.btn_newton.clicked.connect(lambda: self._set_method("Newton-Raphson"))
        self.btn_secant.clicked.connect(lambda: self._set_method("Secante"))
        self.btn_calc.clicked.connect(self.compute)
        self.btn_plot.clicked.connect(lambda: self.plot_function(explicit=True))
        self.btn_suggest.clicked.connect(self.suggest_interval)
        self.btn_clear.clicked.connect(self._clear)
        self.func.textChanged.connect(self.update_preview)
        self.slider_font.valueChanged.connect(lambda v: self.log.setFont(QtGui.QFont("Consolas", v)))
        self._set_method("Bisección"); self.update_preview()

    def compute(self):
        method = self.current_method
        func = self.func.text().strip()
        if not func:
            self.log.setPlainText("Ingresa una función para continuar.")
            return
        tol = self.tol.value(); max_it = self.max_iter.value(); a = self.a.value(); b = self.b.value()
        try:
            if method == "Bisección":
                data = self._bisection(func, a, b, tol, max_it); params = {"a": data["interval"][0], "b": data["interval"][1]}
            elif method == "Falsa Posición":
                data = self._false_position(func, a, b, tol, max_it); params = {"a": data["interval"][0], "b": data["interval"][1]}
            elif method == "Newton-Raphson":
                data = self._newton(func, a, tol, max_it); params = {"x0": a}
            else:
                data = self._secant(func, a, b, tol, max_it); params = {"x0": a, "x1": b}
            report = self._build_result_text(method, func, tol, max_it, data, params)
            self.log.setPlainText(report)
            self.last_root = data["root"]; self.last_func = func; self.last_params = {"method": method, **params}
            self._plot_function(method, func, params, data["root"])
        except ValueError as err:
            self.log.setPlainText(str(err))
            self.plot_ax.clear(); self.plot_ax.text(0.5, 0.5, "Cálculo no disponible", ha="center", va="center", color="#FF453A")
            self.plot_ax.set_axis_off(); self.canvas.draw_idle()

    def _bisection(self, func, a, b, tol, max_it):
        original = (a, b); fa = self._eval(a, func); fb = self._eval(b, func)
        if fa * fb > 0:
            interval = self._auto_interval(func, a, b)
            if interval is None:
                raise ValueError("La función no cambia de signo en el intervalo dado.")
            a, b = interval; fa = self._eval(a, func); fb = self._eval(b, func)
        rows = []; prev_c = None
        for it in range(1, max_it + 1):
            c = (a + b) / 2; fc = self._eval(c, func); ea = abs(c - prev_c) if prev_c is not None else None
            rows.append((it, a, b, c, fa, fb, fc, abs(b - a) / 2))
            if abs(fc) <= tol or abs(b - a) / 2 <= tol:
                prev_c = c; break
            if fa * fc < 0: b, fb = c, fc
            else: a, fa = c, fc
            prev_c = c
        root = prev_c if prev_c is not None else (a + b) / 2
        return {"root": root, "f_root": self._eval(root, func), "rows": rows, "formats": ["d"] + ["float"] * 7, "interval": (a, b), "original": original}

    def _false_position(self, func, a, b, tol, max_it):
        original = (a, b); fa = self._eval(a, func); fb = self._eval(b, func)
        if fa * fb > 0:
            interval = self._auto_interval(func, a, b)
            if interval is None:
                raise ValueError("La función no cambia de signo en el intervalo dado.")
            a, b = interval; fa = self._eval(a, func); fb = self._eval(b, func)
        rows = []; prev_c = None
        for it in range(1, max_it + 1):
            fa = self._eval(a, func); fb = self._eval(b, func)
            if abs(fb - fa) < 1e-14:
                raise ValueError("f(a) y f(b) casi iguales; el método se vuelve inestable.")
            c = b - fb * (b - a) / (fb - fa); fc = self._eval(c, func); ea = abs(c - prev_c) if prev_c is not None else None
            rows.append((it, a, b, c, fa, fb, fc, ea))
            if abs(fc) <= tol or (ea is not None and ea <= tol):
                prev_c = c; break
            if fa * fc < 0: b = c
            else: a = c
            prev_c = c
        root = prev_c if prev_c is not None else (a + b) / 2
        return {"root": root, "f_root": self._eval(root, func), "rows": rows, "formats": ["d"] + ["float"] * 7, "interval": (a, b), "original": original}

    def _newton(self, func, x0, tol, max_it):
        rows = []; x = x0
        for it in range(1, max_it + 1):
            fx = self._eval(x, func); dfx = self._derivative(x, func)
            if abs(dfx) < 1e-14:
                raise ValueError("Derivada cercana a cero; elige otro valor inicial.")
            x_next = x - fx / dfx; ea = abs(x_next - x)
            rows.append((it, x, fx, dfx, ea)); x = x_next
            if ea <= tol or abs(self._eval(x, func)) <= tol:
                break
        return {"root": x, "f_root": self._eval(x, func), "rows": rows, "formats": ["d"] + ["float"] * 4, "interval": (x, x), "original": (x0, None)}

    def _secant(self, func, x0, x1, tol, max_it):
        rows = []; a, b = x0, x1; fa = self._eval(a, func); fb = self._eval(b, func)
        if abs(fb - fa) < 1e-14:
            raise ValueError("f(x0) y f(x1) casi iguales; el método de la secante falla.")
        for it in range(1, max_it + 1):
            if abs(fb - fa) < 1e-14:
                raise ValueError("División por cero durante las iteraciones de Secante.")
            c = b - fb * (b - a) / (fb - fa); fc = self._eval(c, func); ea = abs(c - b)
            rows.append((it, a, b, c, fc, ea))
            if ea <= tol or abs(fc) <= tol:
                b = c; break
            a, b = b, c; fa, fb = fb, fc
        return {"root": b, "f_root": self._eval(b, func), "rows": rows, "formats": ["d"] + ["float"] * 5, "interval": (a, b), "original": (x0, x1)}

    def _build_result_text(self, method, func, tol, max_it, data, params):
        fmt_func = math_utils.format_function_display(func)
        lines = [
            f"MÉTODO DE {method.upper()}",
            f"Función: f(x) = {fmt_func}",
            f"Tolerancia: {tol:.4g}",
            f"Máx. iteraciones: {max_it}",
        ]
        if method in ("Bisección", "Falsa Posición"):
            lines.append(f"Intervalo inicial: [{params['a']:.6f}, {params['b']:.6f}]")
            if tuple(params.values()) != data["original"]:
                oa, ob = data["original"]; lines.append(f"Intervalo ajustado automáticamente desde [{oa:.6f}, {ob:.6f}]")
        elif method == "Newton-Raphson":
            lines.append(f"x₀: {params['x0']:.6f}")
        else:
            lines.append(f"x₀: {params['x0']:.6f}")
            lines.append(f"x₁: {params['x1']:.6f}")
        lines.append(""); lines.append("TABLA DE ITERACIONES:")
        lines.extend(self._format_table(method, data["rows"], data["formats"]))
        root = data["root"]; lines.append(""); lines.append(f"RESULTADO FINAL ({method}):")
        lines.append(f"Raíz aproximada x = {root:.10f}")
        lines.append(f"f({root:.10f}) = {data['f_root']:.3e}")
        lines.append(f"Iteraciones ejecutadas: {len(data['rows'])}")
        return "\n".join(lines)

    def _format_table(self, method, rows, formats):
        headers = {
            "Bisección": ["Iter", "a", "b", "c", "f(a)", "f(b)", "f(c)", "ea"],
            "Falsa Posición": ["Iter", "a", "b", "c", "f(a)", "f(b)", "f(c)", "ea"],
            "Newton-Raphson": ["Iter", "x", "f(x)", "f'(x)", "ea"],
            "Secante": ["Iter", "x₀", "x₁", "x₂", "f(x₂)", "ea"],
        }[method]
        format_rows = []
        for row in rows:
            formatted = []
            for idx, value in enumerate(row):
                fmt = formats[idx] if idx < len(formats) else "float"
                formatted.append(f"{int(value)}" if fmt == "d" else self._format_number(value))
            format_rows.append(formatted)
        widths = [len(h) for h in headers]
        for row in format_rows:
            for idx, cell in enumerate(row):
                widths[idx] = max(widths[idx], len(cell))
        sep = "=" * (sum(widths) + 3 * (len(headers) - 1))
        lines = [sep, "   ".join(headers[i].ljust(widths[i]) for i in range(len(headers))), "-" * len(sep)]
        for row in format_rows:
            lines.append("   ".join(row[i].rjust(widths[i]) for i in range(len(headers))))
        lines.append(sep)
        return lines

    def _format_number(self, value):
        if value is None:
            return "-"
        if math.isfinite(value):
            if abs(value) >= 1e6 or (0 < abs(value) < 1e-6):
                return f"{value:.3e}"
            return f"{value:.10f}"
        return "NaN"

    def _plot_function(self, method, func, params, root):
        self.plot_ax.clear()
        try:
            if method in ("Bisección", "Falsa Posición"):
                base_min, base_max = params["a"], params["b"]
            elif method == "Secante":
                base_min = min(params["x0"], params["x1"]); base_max = max(params["x0"], params["x1"])
            else:
                base_min, base_max = params["x0"] - 5, params["x0"] + 5
            if base_min == base_max:
                base_min -= 5; base_max += 5
            x_min, x_max = self._determine_plot_range(func, base_min, base_max)
            xs = np.linspace(x_min, x_max, 2000)
            ys = math_utils.evaluate_function_vectorized(xs, func)
            ys = np.where(np.isfinite(ys), ys, np.nan)
            self.plot_ax.plot(xs, ys, color="#FFB703", linewidth=2, label="f(x)")
            self.plot_ax.axhline(0, color="#666", linestyle="--", linewidth=1)
            self.plot_ax.axvline(0, color="#666", linestyle="--", linewidth=1)
            if method in ("Bisección", "Falsa Posición"):
                self.plot_ax.axvline(params["a"], color="#30D158", linestyle=":", linewidth=1.4, label=f"a = {params['a']:.3f}")
                self.plot_ax.axvline(params["b"], color="#FF453A", linestyle=":", linewidth=1.4, label=f"b = {params['b']:.3f}")
            elif method == "Secante":
                y0 = self._eval(params["x0"], func); y1 = self._eval(params["x1"], func)
                self.plot_ax.scatter([params["x0"], params["x1"]], [y0, y1], color="#30D158", marker="o", label="Puntos iniciales")
            if root is not None and math.isfinite(root):
                fr = self._eval(root, func)
                self.plot_ax.plot(root, fr, "o", color="#BB33FF", markersize=8, label=f"Raíz ≈ {root:.4f}")
                self.plot_ax.axvline(root, color="#BB33FF", linestyle="--", linewidth=1.2)
            try:
                low, high = np.nanpercentile(ys, [1, 99])
                if np.isfinite(low) and np.isfinite(high) and high > low:
                    pad = 0.1 * (high - low)
                    self.plot_ax.set_ylim(low - pad, high + pad)
            except Exception:
                pass
            self.plot_ax.set_xlim(x_min, x_max)
            self.plot_ax.set_xlabel("x"); self.plot_ax.set_ylabel("f(x)")
            self.plot_ax.grid(True, linestyle="--", alpha=0.35); self.plot_ax.legend()
        except Exception as err:
            self.plot_ax.clear()
            self.plot_ax.text(0.5, 0.5, f"No se pudo graficar:\n{err}", ha="center", va="center", color="#FF453A")
            self.plot_ax.set_axis_off()
        self.figure.tight_layout(); self.canvas.draw_idle()

    def _eval(self, x, func):
        return math_utils.evaluate_function(x, func)

    def _derivative(self, x, func, h=1e-6):
        return (self._eval(x + h, func) - self._eval(x - h, func)) / (2 * h)

    def _auto_interval(self, func, a, b):
        res = self._suggest_interval_core(func)
        if res is None:
            return None
        return res[0], res[1]

    def _suggest_interval_core(self, func, prefer_zero=True):
        search_specs = [(-10, 10, 0.1), (-50, 50, 0.2), (-100, 100, 0.5)]
        intervals = []; zeros = []
        for start, end, step in search_specs:
            prev_x = prev_y = None
            x = start
            while x <= end:
                try:
                    y = self._eval(x, func)
                except Exception:
                    prev_x = prev_y = None; x = round(x + step, 10); continue
                if not math.isfinite(y):
                    prev_x = prev_y = None; x = round(x + step, 10); continue
                if abs(y) < 1e-12:
                    zeros.append((x, step))
                if prev_y is not None and prev_y * y < 0:
                    intervals.append((prev_x, x))
                    if len(intervals) >= 32:
                        break
                prev_x, prev_y = x, y
                x = round(x + step, 10)
            if intervals or zeros:
                break
        if not intervals and not zeros:
            return None
        if zeros and prefer_zero:
            zx, st = sorted(zeros, key=lambda z: abs(z[0]))[0]
            return zx - st, zx + st, intervals, zeros
        best = sorted(intervals, key=lambda ab: (abs(sum(ab) / 2), abs(ab[1] - ab[0])))[0]
        return best[0], best[1], intervals, zeros

    def _determine_plot_range(self, func, base_min, base_max):
        try:
            res = self._suggest_interval_core(func, prefer_zero=False)
            if res:
                a, b, intervals, _ = res
                xs = [a, b] + [v for pair in intervals for v in pair]
                x_min = min(xs) - 2; x_max = max(xs) + 2
            else:
                x_min, x_max = base_min, base_max
            if x_max - x_min < 10:
                mid = (x_min + x_max) / 2
                x_min, x_max = mid - 5, mid + 5
            return max(-100, x_min), min(100, x_max)
        except Exception:
            return base_min - 2, base_max + 2

    def _set_method(self, name):
        self.current_method = name
        for method, btn in self.method_buttons.items():
            if method == name:
                btn.setStyleSheet(f"background:{self.colors['accent']}; color:black; border-radius:6px; padding:8px 12px; font-weight:bold;")
            else:
                btn.setStyleSheet(f"background:{self.colors['secondary_bg']}; color:{self.colors['text']}; border-radius:6px; padding:8px 12px;")
        self.b.setEnabled(name != "Newton-Raphson")

    def insert_text(self, value):
        if value == "<DEL>":
            self.func.backspace()
            return
        pos = self.func.cursorPosition()
        text = self.func.text()
        self.func.setText(text[:pos] + value + text[pos:])
        self.func.setCursorPosition(pos + len(value))

    def update_preview(self):
        self.preview_ax.clear(); self.preview_ax.axis("off")
        func = self.func.text().strip()
        if func:
            latex = self._to_mathtext(func)
            self.preview_ax.text(0.02, 0.5, f"$f(x) = {latex}$", fontsize=13, va="center")
        self.preview_fig.tight_layout(); self.preview_canvas.draw_idle()

    def _to_mathtext(self, s):
        tmp = s.replace("π", "pi").replace(" ", "")
        tmp = re.sub(r"sqrt\(([^)]+)\)", r"\\sqrt{\1}", tmp)
        tmp = re.sub(r"([A-Za-z0-9\)]+)\^([A-Za-z0-9\(\-]+)", r"\1^{\2}", tmp)
        tmp = tmp.replace("*", "")
        return tmp

    def plot_function(self, explicit=False):
        func = self.func.text().strip()
        if not func:
            self.log.appendPlainText("Ingresa una función para graficar.")
            return
        method = self.current_method
        if explicit or not self.last_params or self.last_func != func:
            if method in ("Bisección", "Falsa Posición"):
                params = {"a": self.a.value(), "b": self.b.value()}
            elif method == "Newton-Raphson":
                params = {"x0": self.a.value()}
            else:
                params = {"x0": self.a.value(), "x1": self.b.value()}
        else:
            params = {k: v for k, v in self.last_params.items() if k != "method"}
            method = self.last_params.get("method", method)
        root = self.last_root if self.last_func == func else None
        self._plot_function(method, func, params, root)

    def suggest_interval(self):
        func = self.func.text().strip()
        if not func:
            self.log.appendPlainText("Ingresa una función para sugerir intervalos.")
            return
        res = self._suggest_interval_core(func)
        if res is None:
            self.log.appendPlainText("No se encontró cambio de signo en el rango analizado.")
            return
        a, b, intervals, zeros = res
        self.a.setValue(a); self.b.setValue(b)
        report = ["Intervalos con cambio de signo:"]
        for idx, (ia, ib) in enumerate(intervals, 1):
            report.append(f"{idx:>2}. [{ia:.6f}, {ib:.6f}]")
        if zeros:
            report.append(""); report.append("Posibles raíces exactas:")
            for idx, (zx, step) in enumerate(sorted(zeros, key=lambda z: abs(z[0])), 1):
                report.append(f"{idx:>2}. x ≈ {zx:.6f}  (usar [{zx-step:.6f}, {zx+step:.6f}])")
        self.log.setPlainText("\n".join(report))

    def _clear(self):
        self.func.clear(); self.a.setValue(-1.0); self.b.setValue(1.0); self.tol.setValue(1e-4); self.max_iter.setValue(100)
        self.log.clear(); self.last_root = None; self.last_func = ""; self.last_params = {}
        self.plot_ax.clear(); self.plot_ax.axhline(0, color="#666", linestyle="--", linewidth=1)
        self.plot_ax.axvline(0, color="#666", linestyle="--", linewidth=1); self.canvas.draw_idle()
        self.update_preview()

class InicioPage(QWidget):
    def __init__(self, colors, tabs, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.tabs = tabs
        layout = QVBoxLayout(self); layout.setContentsMargins(24,24,24,24); layout.setSpacing(16)
        title = QLabel("Suite de Álgebra Computacional")
        title.setStyleSheet(f"color:{colors['accent']};"); title.setFont(QtGui.QFont("Segoe UI", 26, QtGui.QFont.Bold))
        subtitle = QLabel("Seleccione el módulo")
        subtitle.setStyleSheet(f"color:{colors['text_secondary']};"); subtitle.setFont(QtGui.QFont("Segoe UI", 12))
        layout.addWidget(title, alignment=Qt.AlignLeft)
        layout.addWidget(subtitle, alignment=Qt.AlignLeft)
        grid = QGridLayout(); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(8)
        layout.addLayout(grid)
        def mk_btn(text, tab_index, primary=False):
            btn = QPushButton(text); btn.setMinimumHeight(44)
            style_primary = f"background:{colors['accent']}; color:black; border:0; border-radius:8px; padding:10px 16px; font-weight:bold;"
            style_secondary = f"background:{colors['secondary_bg']}; color:{colors['text']}; border:0; border-radius:8px; padding:10px 16px;"
            btn.setStyleSheet(style_primary if primary else style_secondary)
            btn.clicked.connect(lambda: self.tabs.setCurrentIndex(tab_index))
            return btn
        grid.addWidget(mk_btn("Matrices", 1, True), 0, 0)
        grid.addWidget(mk_btn("Gauss‑Jordan", 2, True), 0, 1)
        grid.addWidget(mk_btn("Métodos Numéricos", 3, False), 1, 0)
        grid.addWidget(QWidget(), 1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        grid.setRowStretch(2, 1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.colors = {
            "background": "#2B2D42",
            "secondary_bg": "#3C3F58",
            "accent": "#FF9F0A",
            "text": "#FFFFFF",
            "text_secondary": "#E5E5E7",
            "button_secondary": "#6C757D",
            "matrix_bg": "#353849"
        }
        self.setWindowTitle("Calculadora de Álgebra (Interfaz Moderna)")
        self.resize(1200, 850)
        central = QWidget(); self.setCentralWidget(central)
        v = QVBoxLayout(central); v.setContentsMargins(0,0,0,0); v.setSpacing(0)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(False)
        v.addWidget(self.tabs)
        self.apply_style()
        inicio = InicioPage(self.colors, self.tabs)
        matrices = MatricesPage(self.colors)
        gauss = GaussJordanPage(self.colors)
        roots = RootFindingPage(self.colors)
        self.tabs.addTab(inicio, "Inicio")
        self.tabs.addTab(matrices, "Matrices")
        self.tabs.addTab(gauss, "Gauss‑Jordan")
        self.tabs.addTab(roots, "Raíces")

    def apply_style(self):
        QApplication.setStyle("Fusion")
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Window, QtGui.QColor(self.colors["background"]))
        pal.setColor(QtGui.QPalette.WindowText, QtGui.QColor(self.colors["text"]))
        pal.setColor(QtGui.QPalette.Base, QtGui.QColor(self.colors["secondary_bg"]))
        pal.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(self.colors["matrix_bg"]))
        pal.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(self.colors["secondary_bg"]))
        pal.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(self.colors["text"]))
        pal.setColor(QtGui.QPalette.Text, QtGui.QColor(self.colors["text"]))
        pal.setColor(QtGui.QPalette.Button, QtGui.QColor(self.colors["secondary_bg"]))
        pal.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(self.colors["text"]))
        pal.setColor(QtGui.QPalette.BrightText, Qt.red)
        pal.setColor(QtGui.QPalette.Highlight, QtGui.QColor(self.colors["accent"]))
        pal.setColor(QtGui.QPalette.HighlightedText, Qt.black)
        self.setPalette(pal)
        self.setStyleSheet(f"""
            QTabWidget::pane {{ border: 0; background:{self.colors['background']}; }}
            QTabBar::tab {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; padding:10px 16px; margin:4px; border-radius:6px; }}
            QTabBar::tab:selected {{ background:{self.colors['accent']}; color:black; }}
            QLabel {{ color:{self.colors['text']}; }}
            QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{ background:{self.colors['matrix_bg']}; color:{self.colors['text']}; border:1px solid {self.colors['secondary_bg']}; border-radius:4px; padding:4px 6px; }}
            QPushButton {{ background:{self.colors['accent']}; color:black; border:0; border-radius:6px; padding:10px 16px; font-weight:bold; }}
        """)

def main():
    app = QApplication([])
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    w = MainWindow()
    w.showMaximized()
    app.exec()