import sys
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit, QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QAbstractScrollArea, QScrollArea, QSlider, QSizePolicy, QButtonGroup, QMessageBox, QAbstractSpinBox
from PySide6.QtCore import Qt
from fractions import Fraction
import math
import numpy as np
import re
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import sympy as sp
from matrix_core import Matrix, fraction_to_str
import operations_sum, operations_subtract, operations_multiply, operations_determinant, operations_cofactor, operations_gauss, root_bisection, root_falsepos, math_utils

DEFAULT_COLORS = {
    "accent": "#FF9500",
    "text": "#F2F2F7",
    "text_secondary": "#8E8E93",
    "secondary_bg": "rgba(28, 28, 30, 0.85)",
    "matrix_bg": "rgba(44, 44, 46, 0.92)",
}

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
        self.rowsB = 3
        self.colsA = 3
        self.colsB = 3
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel("Operaciones con Matrices")
        title.setStyleSheet(f"color:{colors['accent']};")
        title.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold))
        layout.addWidget(title, alignment=Qt.AlignLeft)

        wrapper = QHBoxLayout(); wrapper.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.addLayout(wrapper)

        control_card = QFrame(); control_card.setObjectName("matrixControlsCard")
        control_card.setStyleSheet(
            """
            QFrame#matrixControlsCard {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
            }
            """
        )
        control_card.setFixedWidth(760)
        card = QVBoxLayout(control_card); card.setContentsMargins(18, 18, 18, 18); card.setSpacing(14)
        wrapper.addWidget(control_card)

        self.expr_input = QLineEdit()
        self.expr_input.setPlaceholderText("Expresión (ej. 2A+3B, A-B, A+2A)")
        self.expr_input.setFixedWidth(320)
        self.expr_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.view_mode = QComboBox()
        self.view_mode.addItems(["Apilada", "Lado a lado"])
        self.view_mode.setFixedWidth(170)
        self.view_mode.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.view_mode.setCursor(Qt.PointingHandCursor)

        combo_style = f"""
            QComboBox {{
                color: {self.colors['text']};
                background-color: {self.colors['secondary_bg']};
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 14px;
                padding: 6px 14px;
            }}
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid rgba(255, 255, 255, 0.18);
            }}
            QComboBox::down-arrow {{
                width: 0;
                height: 0;
                margin-right: 10px;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 7px solid {self.colors['accent']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.colors['matrix_bg']};
                color: {self.colors['text']};
                selection-background-color: {self.colors['accent']};
                selection-color: #000000;
            }}
        """
        line_style = f"""
            QLineEdit {{
                color: {self.colors['text']};
                background-color: {self.colors['secondary_bg']};
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 14px;
                padding: 6px 14px;
            }}
        """
        self.expr_input.setStyleSheet(line_style)
        self.view_mode.setStyleSheet(combo_style)

        spin_style = f"""
            QSpinBox {{
                color: {self.colors['text']};
                background-color: {self.colors['matrix_bg']};
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 8px;
                padding: 4px 8
            }}
        """
        self.spin_rows = QSpinBox(); self.spin_rows.setRange(1, 10); self.spin_rows.setValue(self.rows); self.spin_rows.setStyleSheet(spin_style); self.spin_rows.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_colsA = QSpinBox(); self.spin_colsA.setRange(1, 10); self.spin_colsA.setValue(self.colsA); self.spin_colsA.setStyleSheet(spin_style); self.spin_colsA.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_rowsB = QSpinBox(); self.spin_rowsB.setRange(1, 10); self.spin_rowsB.setValue(self.rowsB); self.spin_rowsB.setStyleSheet(spin_style); self.spin_rowsB.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin_colsB = QSpinBox(); self.spin_colsB.setRange(1, 10); self.spin_colsB.setValue(self.colsB); self.spin_colsB.setStyleSheet(spin_style); self.spin_colsB.setButtonSymbols(QAbstractSpinBox.NoButtons)
        for spin in (self.spin_rows, self.spin_colsA, self.spin_rowsB, self.spin_colsB):
            spin.hide()

        # Operaciones: barra superior (crear antes de usar en toolbar)
        self.basic_op = QComboBox(); self.basic_op.addItems(["Expresión", "Suma", "Resta", "Multiplicación", "Escalar"])
        self.basic_op.setFixedWidth(160); self.basic_op.setCursor(Qt.PointingHandCursor); self.basic_op.setStyleSheet(combo_style)
        self.adv_op = QComboBox(); self.adv_op.addItems(["Ninguna", "Transpuesta", "Inversa", "Diagonal Superior", "Diagonal Inferior", "Determinante", "Cofactor"])
        self.adv_op.setFixedWidth(170); self.adv_op.setCursor(Qt.PointingHandCursor); self.adv_op.setStyleSheet(combo_style)
        self.scalar_input = QLineEdit(); self.scalar_input.setPlaceholderText("k"); self.scalar_input.setFixedWidth(70); self.scalar_input.setStyleSheet(line_style)
        self.scalar_input.hide()

        toolbar = QGridLayout(); toolbar.setHorizontalSpacing(4); toolbar.setVerticalSpacing(4)
        # Fila 1: Básicas y Avanzadas en la misma columna de pares (label/combos)
        toolbar.addWidget(QLabel("Básicas:"), 0, 0)
        toolbar.addWidget(self.basic_op, 0, 1)
        toolbar.addWidget(QLabel("Avanzadas:"), 0, 2)
        toolbar.addWidget(self.adv_op, 0, 3)
        toolbar.addWidget(self.scalar_input, 0, 4)
        # Fila 2: Expresión y Vista exactamente debajo de sus columnas
        lbl_operation = QLabel("Expresión:"); lbl_operation.setStyleSheet(f"color:{self.colors['text_secondary']}; font-weight:600;")
        toolbar.addWidget(lbl_operation, 1, 0)
        self.expr_input.setFixedWidth(200)
        toolbar.addWidget(self.expr_input, 1, 1)
        lbl_view = QLabel("Vista:"); lbl_view.setStyleSheet(f"color:{self.colors['text_secondary']}; font-weight:600;")
        toolbar.addWidget(lbl_view, 1, 2)
        toolbar.addWidget(self.view_mode, 1, 3)
        toolbar.setColumnStretch(1, 2); toolbar.setColumnStretch(3, 1)
        card.addLayout(toolbar)

        btns = QHBoxLayout(); btns.setSpacing(10); btns.setAlignment(Qt.AlignRight)
        self.btn_generate = QPushButton("Generar Tablas")
        self.btn_solve = QPushButton("Resolver")
        self.btn_clear = QPushButton("Limpiar")
        for b in (self.btn_generate, self.btn_solve, self.btn_clear):
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedSize(110, 36)
        btns.addWidget(self.btn_generate); btns.addWidget(self.btn_solve); btns.addWidget(self.btn_clear)
        layout.addLayout(btns)
        self.body = QVBoxLayout(); self.body.setSpacing(16); layout.addLayout(self.body)
        self.view_mode.currentTextChanged.connect(self._on_view_mode)
        self.view_mode.setCurrentIndex(1)
        self.btn_generate.clicked.connect(self.generate_tables)
        self.btn_clear.clicked.connect(self.clear_all)
        self.btn_solve.clicked.connect(self.solve_expression)

        self.spin_rows.valueChanged.connect(lambda _: self.generate_tables())
        self.spin_colsA.valueChanged.connect(lambda _: self.generate_tables())
        self.spin_rowsB.valueChanged.connect(lambda _: self.generate_tables())
        self.spin_colsB.valueChanged.connect(lambda _: self.generate_tables())
        # Elementos ya colocados en toolbar

        self.basic_op.currentTextChanged.connect(lambda t: self.scalar_input.setVisible(t == "Escalar"))
        self.apply_palette()
        self.generate_tables()

    def apply_palette(self):
        self.setStyleSheet(f"""
            QTableWidget {{ background-color: {self.colors['matrix_bg']}; color: {self.colors['text']}; gridline-color: {self.colors['secondary_bg']}; selection-background-color: {self.colors['accent']}; }}
            QHeaderView::section {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; padding:6px; border:0px; }}
            QLabel {{ color:{self.colors['text']}; }}
            QPlainTextEdit {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; border:1px solid {self.colors['secondary_bg']}; }}
        """)

    def _on_view_mode(self, text):
        self.build_body(text == "Apilada")

    def _adjust_columns(self, delta):
        self.spin_colsA.setValue(max(1, self.spin_colsA.value() + delta))
        self.spin_colsB.setValue(max(1, self.spin_colsB.value() + delta))

    def _adjust_rows(self, delta):
        self.spin_rows.setValue(max(1, self.spin_rows.value() + delta))
        self.spin_rowsB.setValue(max(1, self.spin_rowsB.value() + delta))

    def _set_table_rows(self, table: QTableWidget, target: int):
        while table.rowCount() < target:
            new_row = table.rowCount()
            table.insertRow(new_row)
            for c in range(table.columnCount()):
                if not table.item(new_row, c):
                    table.setItem(new_row, c, QTableWidgetItem(""))
        while table.rowCount() > target and table.rowCount() > 1:
            table.removeRow(table.rowCount() - 1)
        self._auto_resize_table(table)

    def _set_table_columns(self, table: QTableWidget, target: int):
        while table.columnCount() < target:
            new_col = table.columnCount()
            table.insertColumn(new_col)
            for r in range(table.rowCount()):
                if not table.item(r, new_col):
                    table.setItem(r, new_col, QTableWidgetItem(""))
        while table.columnCount() > target and table.columnCount() > 1:
            table.removeColumn(table.columnCount() - 1)
        self._auto_resize_table(table)

    def _adjust_table_rows(self, table: QTableWidget, spin: QSpinBox, delta: int):
        new_value = max(1, spin.value() + delta)
        spin.blockSignals(True)
        spin.setValue(new_value)
        spin.blockSignals(False)
        self._set_table_rows(table, new_value)

    def _adjust_table_cols(self, table: QTableWidget, spin: QSpinBox, delta: int):
        new_value = max(1, spin.value() + delta)
        spin.blockSignals(True)
        spin.setValue(new_value)
        spin.blockSignals(False)
        self._set_table_columns(table, new_value)

    def generate_tables(self):
        self.rows = self.spin_rows.value()
        self.colsA = self.spin_colsA.value()
        self.rowsB = self.spin_rowsB.value()
        self.colsB = self.spin_colsB.value()
        self.build_body(self.view_mode.currentText() == "Apilada")

    def build_body(self, stacked: bool):
        self._clear_layout(self.body)
        # QTabWidget interno
        self.inner_tabs = QTabWidget()
        self.inner_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.inner_tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{ border: 1px solid rgba(255,255,255,0.10); border-radius: 12px; }}
            QTabBar::tab {{ background: rgba(255,255,255,0.06); color: {self.colors['text']}; padding: 6px 12px; border-radius: 10px; margin: 2px; }}
            QTabBar::tab:selected {{ background: {self.colors['accent']}; color: black; }}
            QTabBar::tab:hover {{ background: rgba(255,255,255,0.10); }}
            """
        )
        self.body.addWidget(self.inner_tabs)

        # Tab 1: Matrices
        self.tab_matrices = QWidget(); self.tab_matrices_layout = QVBoxLayout(self.tab_matrices); self.tab_matrices_layout.setSpacing(12); self.tab_matrices_layout.setContentsMargins(10,10,10,10); self.tab_matrices_layout.setAlignment(Qt.AlignTop)
        self.tableA = QTableWidget(self.rows, self.colsA)
        self.tableB = QTableWidget(self.rowsB, self.colsB)
        for table in (self.tableA, self.tableB):
            table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            table.setMinimumHeight(180)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setDefaultSectionSize(32)
            table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sectionA = QVBoxLayout(); sectionA.setSpacing(8)
        sectionA.addWidget(QLabel("Matriz A")); sectionA.addWidget(self.tableA)
        controlsA = QHBoxLayout(); controlsA.setSpacing(6); controlsA.setContentsMargins(0, 0, 0, 0); controlsA.setAlignment(Qt.AlignLeft)
        btn_a_sub_row = QPushButton("− Fila"); btn_a_add_row = QPushButton("+ Fila")
        btn_a_sub_col = QPushButton("− Col"); btn_a_add_col = QPushButton("+ Col")
        for b in (btn_a_sub_row, btn_a_add_row, btn_a_sub_col, btn_a_add_col):
            b.setFixedSize(74, 26); b.setCursor(Qt.PointingHandCursor); controlsA.addWidget(b)
        sectionA.addLayout(controlsA)

        sectionB = QVBoxLayout(); sectionB.setSpacing(8)
        sectionB.addWidget(QLabel("Matriz B")); sectionB.addWidget(self.tableB)
        controlsB = QHBoxLayout(); controlsB.setSpacing(6); controlsB.setContentsMargins(0, 0, 0, 0); controlsB.setAlignment(Qt.AlignLeft)
        btn_b_sub_row = QPushButton("− Fila"); btn_b_add_row = QPushButton("+ Fila")
        btn_b_sub_col = QPushButton("− Col"); btn_b_add_col = QPushButton("+ Col")
        for b in (btn_b_sub_row, btn_b_add_row, btn_b_sub_col, btn_b_add_col):
            b.setFixedSize(74, 26); b.setCursor(Qt.PointingHandCursor); controlsB.addWidget(b)
        sectionB.addLayout(controlsB)

        self.containerA = QWidget(); self.containerA.setLayout(sectionA)
        self.containerB = QWidget(); self.containerB.setLayout(sectionB)
        if stacked:
            matrices_layout = QVBoxLayout(); matrices_layout.setSpacing(12)
            matrices_layout.addWidget(self.containerA); matrices_layout.addWidget(self.containerB)
        else:
            matrices_layout = QHBoxLayout(); matrices_layout.setSpacing(18)
            matrices_layout.addWidget(self.containerA, 1); matrices_layout.addWidget(self.containerB, 1)
            matrices_layout.setStretch(0, 1); matrices_layout.setStretch(1, 1)
        matrices_layout.setAlignment(Qt.AlignTop)
        self.matrices_layout = matrices_layout
        matrices_card = QFrame(); matrices_card.setObjectName("matricesCard")
        matrices_card.setStyleSheet("""
            QFrame#matricesCard { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; }
        """)
        matrices_card_lay = QVBoxLayout(matrices_card); matrices_card_lay.setContentsMargins(12,12,12,12); matrices_card_lay.setSpacing(10); matrices_card_lay.setAlignment(Qt.AlignTop)
        matrices_card_lay.addLayout(matrices_layout)
        try:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            shadow = QGraphicsDropShadowEffect(matrices_card); shadow.setBlurRadius(16); shadow.setColor(QtGui.QColor(0,0,0,64)); shadow.setOffset(0,3)
            matrices_card.setGraphicsEffect(shadow)
        except Exception:
            pass
        self.tab_matrices_layout.addWidget(matrices_card)
        self.tab_matrices_layout.addStretch(1)

        self.inner_tabs.addTab(self.tab_matrices, "Matrices")

        # Tab 2: Paso a Paso
        self.tab_steps = QWidget(); steps_container_layout = QVBoxLayout(self.tab_steps); steps_container_layout.setContentsMargins(8,8,8,8); steps_container_layout.setAlignment(Qt.AlignTop)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_container = QWidget(); self.steps_layout = QVBoxLayout(scroll_container)
        self.steps_layout.setContentsMargins(8, 8, 8, 8); self.steps_layout.setSpacing(10); self.steps_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(scroll_container)
        steps_container_layout.addWidget(self.scroll_area)
        self.inner_tabs.addTab(self.tab_steps, "Paso a Paso")

        # Resultado Final se muestra dentro de Paso a Paso; se elimina pestaña dedicada

        self._auto_resize_table(self.tableA); self._auto_resize_table(self.tableB)
        btn_a_add_row.clicked.connect(lambda: self._adjust_table_rows(self.tableA, self.spin_rows, 1))
        btn_a_sub_row.clicked.connect(lambda: self._adjust_table_rows(self.tableA, self.spin_rows, -1))
        btn_a_add_col.clicked.connect(lambda: self._adjust_table_cols(self.tableA, self.spin_colsA, 1))
        btn_a_sub_col.clicked.connect(lambda: self._adjust_table_cols(self.tableA, self.spin_colsA, -1))
        btn_b_add_row.clicked.connect(lambda: self._adjust_table_rows(self.tableB, self.spin_rowsB, 1))
        btn_b_sub_row.clicked.connect(lambda: self._adjust_table_rows(self.tableB, self.spin_rowsB, -1))
        btn_b_add_col.clicked.connect(lambda: self._adjust_table_cols(self.tableB, self.spin_colsB, 1))
        btn_b_sub_col.clicked.connect(lambda: self._adjust_table_cols(self.tableB, self.spin_colsB, -1))
        self._auto_resize_table(self.tableA)
        self._auto_resize_table(self.tableB)

        self.steps_layout.addStretch(1)
        self.adv_op.currentTextChanged.connect(self._update_matrix_visibility)
        self._update_matrix_visibility()

    def read_matrix(self, table) -> Matrix:
        rows = table.rowCount(); cols = table.columnCount(); data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                item = table.item(r, c); text = item.text() if item else "0"
                row.append(parse_fraction(text))
            data.append(row)
        return Matrix(data)

    def _update_matrix_visibility(self):
        show_b = self.adv_op.currentText() == "Ninguna"
        if hasattr(self, 'containerB'):
            self.containerB.setVisible(show_b)

    def _matrix_scale(self, mat: Matrix, k: Fraction) -> Matrix:
        rows, cols = mat.shape
        out = [[mat[i, j] * k for j in range(cols)] for i in range(rows)]
        return Matrix(out)

    def _matrix_add(self, A: Matrix, B: Matrix) -> Matrix:
        if A.shape != B.shape:
            raise ValueError("Dimensiones no coinciden para suma")
        rows, cols = A.shape
        out = [[A[i, j] + B[i, j] for j in range(cols)] for i in range(rows)]
        return Matrix(out)

    def _to_sympy(self, mat: Matrix) -> sp.Matrix:
        def to_rat(x):
            if isinstance(x, Fraction):
                return sp.Rational(x.numerator, x.denominator)
            try:
                return sp.Rational(str(x))
            except Exception:
                return sp.Float(float(x))
        return sp.Matrix([[to_rat(mat[i, j]) for j in range(mat.cols)] for i in range(mat.rows)])

    def _fmt(self, x) -> str:
        try:
            val = float(x)
        except Exception:
            try:
                val = float(str(x))
            except Exception:
                return str(x)
        s = f"{val:.6f}"
        s = s.rstrip('0').rstrip('.')
        return s

    def _matrix_widget(self, mat: Matrix, compact=True) -> QTableWidget:
        tbl = QTableWidget(mat.rows, mat.cols)
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.verticalHeader().setVisible(False)
        tbl.horizontalHeader().setVisible(False)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        cell_w = 72 if compact else 96
        cell_h = 24 if compact else 30
        tbl.verticalHeader().setDefaultSectionSize(cell_h)
        for c in range(mat.cols):
            tbl.setColumnWidth(c, cell_w)
        for r in range(mat.rows):
            for c in range(mat.cols):
                tbl.setItem(r, c, QTableWidgetItem(self._fmt(mat[r, c])))
        tbl.setFixedHeight(cell_h * mat.rows + 8)
        tbl.setFixedWidth(cell_w * mat.cols + 8)
        tbl.setStyleSheet(f"QTableWidget {{ background-color: {self.colors['matrix_bg']}; color: {self.colors['text']}; gridline-color: rgba(255,255,255,0.12); }}")
        return tbl

    def _add_step_panel(self, title: str, explanation: str, mat: Matrix):
        from PySide6.QtWidgets import QGroupBox
        gb = QGroupBox(title)
        gb.setStyleSheet(
            f"""
            QGroupBox {{ border: 1px solid rgba(255,255,255,0.10); border-radius: 12px; margin-top: 12px; color:{self.colors['accent']}; font-weight:700; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; }}
            """
        )
        row = QHBoxLayout(gb); row.setContentsMargins(10,10,10,10); row.setSpacing(12)
        expl = QLabel(explanation); expl.setWordWrap(True); expl.setStyleSheet(f"color:{self.colors['text']};")
        row.addWidget(expl, 2)
        tbl = self._matrix_widget(mat, compact=False)
        row.addWidget(tbl, 3)
        self.steps_layout.insertWidget(self.steps_layout.count()-1, gb)

    def _parse_expression(self, s: str):
        t = s.replace(" ", "")
        if not t:
            raise ValueError("Ingresa una expresión, ej. 2A+3B")
        pattern = re.compile(r"([+-]?)((?:\d+(?:/\d+)?(?:\.\d+)?))?([AB])")
        pos = 0; terms = []
        for m in pattern.finditer(t):
            if m.start() != pos:
                raise ValueError("Expresión inválida. Usa términos como 2A+3B")
            sign = -1 if m.group(1) == '-' else 1
            num = m.group(2)
            var = m.group(3)
            coef = Fraction(sign) * (parse_fraction(num) if num else Fraction(1))
            terms.append((coef, var))
            pos = m.end()
        if pos != len(t):
            raise ValueError("Expresión contiene símbolos no soportados")
        return terms

    def _mul(self, A: Matrix, B: Matrix) -> Matrix:
        rowsA, colsA = A.shape; rowsB, colsB = B.shape
        if colsA != rowsB:
            raise ValueError("Dimensiones no compatibles para multiplicación")
        out = []
        for i in range(rowsA):
            row = []
            for j in range(colsB):
                s = Fraction(0)
                for k in range(colsA):
                    s += A[i, k] * B[k, j]
                row.append(s)
            out.append(row)
        return Matrix(out)

    def _transpose(self, M: Matrix) -> Matrix:
        return Matrix([[M[j, i] for j in range(M.rows)] for i in range(M.cols)])

    def _inverse(self, M: Matrix) -> Matrix:
        if M.rows != M.cols:
            raise ValueError("La matriz debe ser cuadrada para inversa")
        sm = self._to_sympy(M)
        inv = sm.inv()
        data = []
        for i in range(inv.rows):
            row = []
            for j in range(inv.cols):
                val = inv[i, j]
                if val.is_Rational:
                    row.append(Fraction(int(val.p), int(val.q)))
                else:
                    row.append(Fraction.from_float(float(val)))
            data.append(row)
        return Matrix(data)

    def _upper(self, M: Matrix) -> Matrix:
        return Matrix([[M[i, j] if i <= j else Fraction(0) for j in range(M.cols)] for i in range(M.rows)])

    def _lower(self, M: Matrix) -> Matrix:
        return Matrix([[M[i, j] if i >= j else Fraction(0) for j in range(M.cols)] for i in range(M.rows)])

    def _set_final(self, mat: Matrix):
        from PySide6.QtWidgets import QGroupBox
        gb = QGroupBox("Resultado Final")
        gb.setStyleSheet(
            f"""
            QGroupBox {{ border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; margin-top: 12px; color:{self.colors['accent']}; font-weight:800; }}
            QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; }}
            """
        )
        lay = QHBoxLayout(gb); lay.setContentsMargins(14,14,14,14)
        tbl = self._matrix_widget(mat, compact=False)
        lay.addWidget(tbl)
        # insertar al final del scroll de Paso a Paso, antes del stretch
        self.steps_layout.insertWidget(self.steps_layout.count()-1, gb)

    def _tokenize(self, s: str):
        t = s.replace(" ", "")
        tokens = []
        i = 0
        while i < len(t):
            ch = t[i]
            if ch in '+-*':
                tokens.append(ch); i += 1; continue
            if ch in 'AB':
                tokens.append(ch); i += 1; continue
            # número (entero/frac/decimal)
            j = i
            while j < len(t) and (t[j].isdigit() or t[j] in '/.'): j += 1
            if j == i:
                raise ValueError("Símbolo inválido en expresión")
            tokens.append(t[i:j]); i = j
        return tokens

    def _eval_expression(self, tokens, A: Matrix, B: Matrix):
        self._clear_steps()
        def clone_zero(rows, cols):
            return Matrix([[Fraction(0) for _ in range(cols)] for _ in range(rows)])
        def read_factor(idx):
            coef = Fraction(1)
            var = None
            # opcional coeficiente
            if idx < len(tokens) and (tokens[idx][0].isdigit()):
                coef = parse_fraction(tokens[idx]); idx += 1
            if idx >= len(tokens) or tokens[idx] not in ('A','B'):
                raise ValueError("Se esperaba A o B")
            var = tokens[idx]; idx += 1
            base = A if var == 'A' else B
            # pasos por celda de escalado
            rows, cols = base.shape
            partial = clone_zero(rows, cols)
            for i in range(rows):
                for j in range(cols):
                    partial[i, j] = base[i, j] * coef
                    self._add_step_panel(f"Paso {self._next_step}", f"({var})[{i+1},{j+1}] * {self._fmt(coef)} = {self._fmt(partial[i,j])}", partial)
                    self._next_step += 1
            scaled = partial
            return scaled, idx
        def read_term(idx):
            mat, idx = read_factor(idx)
            while idx < len(tokens) and tokens[idx] == '*':
                idx += 1
                right, idx = read_factor(idx)
                # multiplicación por celda
                rowsA, colsA = mat.shape; rowsB, colsB = right.shape
                if colsA != rowsB:
                    raise ValueError("Dimensiones no compatibles para multiplicación")
                res = clone_zero(rowsA, colsB)
                for i in range(rowsA):
                    for j in range(colsB):
                        s = Fraction(0); terms = []
                        for k in range(colsA):
                            prod = mat[i, k] * right[k, j]
                            s += prod; terms.append(f"{self._fmt(mat[i,k])}·{self._fmt(right[k,j])}")
                        res[i, j] = s
                        self._add_step_panel(f"Paso {self._next_step}", f"res[{i+1},{j+1}] = " + " + ".join(terms) + f" = {self._fmt(s)}", res)
                        self._next_step += 1
                mat = res
            return mat, idx
        # suma/resta con prioridad
        i = 0
        result = None
        sign = 1
        while i < len(tokens):
            if tokens[i] == '+':
                sign = 1; i += 1; continue
            if tokens[i] == '-':
                sign = -1; i += 1; continue
            term, i = read_term(i)
            if sign == -1:
                rows, cols = term.shape
                for r in range(rows):
                    for c in range(cols):
                        term[r, c] = term[r, c] * Fraction(-1)
                        self._add_step_panel(f"Paso {self._next_step}", f"Cambiar signo término[{r+1},{c+1}]", term)
                        self._next_step += 1
            prev = result
            result = term if result is None else self._matrix_add(result, term)
            if prev is None:
                self._add_step_panel(f"Paso {self._next_step}", "Iniciar acumulado", result); self._next_step += 1
            else:
                # suma por celda
                rows, cols = result.shape
                for r in range(rows):
                    for c in range(cols):
                        val = prev[r, c] + term[r, c]
                        prev[r, c] = val
                        self._add_step_panel(f"Paso {self._next_step}", f"acum[{r+1},{c+1}] = {self._fmt(prev[r,c]-term[r,c])} + {self._fmt(term[r,c])} = {self._fmt(val)}", prev)
                        self._next_step += 1
                result = prev
        return result

    def solve_expression(self):
        try:
            matA = self.read_matrix(self.tableA)
            matB = self.read_matrix(self.tableB)
            expr = self.expr_input.text().strip()
            self._clear_steps()
            self._next_step = 1
            # Si hay expresión, evaluarla con precedencia * antes que +/‑
            if expr:
                tokens = self._tokenize(expr)
                res = self._eval_expression(tokens, matA, matB)
                self._set_final(res)
                self.inner_tabs.setCurrentIndex(1)
                return
            # Operaciones básicas sin expresión
            basic = self.basic_op.currentText()
            adv = self.adv_op.currentText()
            base = matA
            if basic == "Suma":
                # suma por celda
                res = Matrix([[Fraction(0) for _ in range(matA.cols)] for _ in range(matA.rows)])
                for i in range(matA.rows):
                    for j in range(matA.cols):
                        res[i, j] = matA[i, j] + matB[i, j]
                        self._add_step_panel(f"Paso {self._next_step}", f"A[{i+1},{j+1}] + B[{i+1},{j+1}] = {self._fmt(res[i,j])}", res); self._next_step += 1
            elif basic == "Resta":
                res = Matrix([[Fraction(0) for _ in range(matA.cols)] for _ in range(matA.rows)])
                for i in range(matA.rows):
                    for j in range(matA.cols):
                        res[i, j] = matA[i, j] - matB[i, j]
                        self._add_step_panel(f"Paso {self._next_step}", f"A[{i+1},{j+1}] − B[{i+1},{j+1}] = {self._fmt(res[i,j])}", res); self._next_step += 1
            elif basic == "Multiplicación":
                # multiplicación por celda
                res = Matrix([[Fraction(0) for _ in range(matB.cols)] for _ in range(matA.rows)])
                for i in range(matA.rows):
                    for j in range(matB.cols):
                        s = Fraction(0); terms = []
                        for k in range(matA.cols):
                            prod = matA[i, k] * matB[k, j]
                            s += prod; terms.append(f"{self._fmt(matA[i,k])}·{self._fmt(matB[k,j])}")
                        res[i, j] = s
                        self._add_step_panel(f"Paso {self._next_step}", f"res[{i+1},{j+1}] = " + " + ".join(terms) + f" = {self._fmt(s)}", res); self._next_step += 1
            elif basic == "Escalar":
                k = parse_fraction(self.scalar_input.text() or "1")
                res = Matrix([[Fraction(0) for _ in range(base.cols)] for _ in range(base.rows)])
                for i in range(base.rows):
                    for j in range(base.cols):
                        res[i, j] = base[i, j] * k
                        self._add_step_panel(f"Paso {self._next_step}", f"A[{i+1},{j+1}] · {self._fmt(k)} = {self._fmt(res[i,j])}", res); self._next_step += 1
            else:
                res = base
            # Operaciones avanzadas
            if adv == "Transpuesta":
                res = self._transpose(res); self._add_step_panel(f"Paso {self._next_step}", "Transponer matriz (res^T)", res); self._next_step += 1
            elif adv == "Inversa":
                res = self._inverse(res); self._add_step_panel(f"Paso {self._next_step}", "Calcular inversa (res^{-1})", res); self._next_step += 1
            elif adv == "Diagonal Superior":
                res = self._upper(res); self._add_step_panel(f"Paso {self._next_step}", "Tomar triangular superior", res); self._next_step += 1
            elif adv == "Diagonal Inferior":
                res = self._lower(res); self._add_step_panel(f"Paso {self._next_step}", "Tomar triangular inferior", res); self._next_step += 1
            elif adv == "Determinante":
                det, _logs = operations_determinant.determinant_with_log(matA.data)
                res = Matrix([[det]])
                self._add_step_panel(f"Paso {self._next_step}", "Determinante de A", res); self._next_step += 1
            elif adv == "Cofactor":
                res, _logs = operations_cofactor.cofactor_matrix(matA)
                self._add_step_panel(f"Paso {self._next_step}", "Matriz de cofactores de A", res); self._next_step += 1
            self._set_final(res)
            self.inner_tabs.setCurrentIndex(1)
        except Exception as e:
            self._show_error_dialog(str(e))

    def clear_all(self):
        for tbl in (self.tableA, self.tableB):
            tbl.clear(); tbl.setRowCount(0); tbl.setColumnCount(0)
        self._clear_steps()

    def _add_row(self, table: QTableWidget):
        r = table.rowCount(); table.insertRow(r)
        for c in range(table.columnCount()):
            table.setItem(r, c, QTableWidgetItem(""))

    def _add_col(self, table: QTableWidget):
        c = table.columnCount(); table.insertColumn(c)
        for r in range(table.rowCount()):
            table.setItem(r, c, QTableWidgetItem(""))

    def _sub_row(self, table: QTableWidget):
        r = table.rowCount()
        if r>0:
            table.removeRow(r-1)

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

    def _clear_steps(self):
        if hasattr(self, 'steps_layout') and self.steps_layout is not None:
            while self.steps_layout.count() > 1:
                item = self.steps_layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

    def _show_error_dialog(self, message: str):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error")
        dlg.setText(message)
        dlg.exec()

    def _auto_resize_table(self, table: QTableWidget):
        if not table:
            return
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setDefaultSectionSize(32)

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
                    try:
                        sval = f"{float(val):.6f}".rstrip('0').rstrip('.')
                    except Exception:
                        sval = str(val)
                    self.log.appendPlainText(f"x{i} = {sval}")
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
        original = (a, b)
        rows = []
        fa = self._eval(a, func)
        fb = self._eval(b, func)
        if fa == 0.0:
            rows.append((1, a, b, a, fa, fb, fa, 0.0))
            return {
                "root": a,
                "f_root": fa,
                "rows": rows,
                "formats": ["d"] + ["float"] * 7,
                "interval": (a, b),
                "original": original,
            }
        if fb == 0.0:
            rows.append((1, a, b, b, fa, fb, fb, 0.0))
            return {
                "root": b,
                "f_root": fb,
                "rows": rows,
                "formats": ["d"] + ["float"] * 7,
                "interval": (a, b),
                "original": original,
            }
        if fa * fb > 0:
            interval = self._auto_interval(func, a, b)
            if interval is None:
                raise ValueError("La función no cambia de signo en el intervalo dado ni en los rangos sugeridos.")
            a, b = interval
            fa = self._eval(a, func)
            fb = self._eval(b, func)
        root = None
        for it in range(1, max_it + 1):
            c = (a + b) / 2.0
            fc = self._eval(c, func)
            error = abs(b - a) / 2.0
            rows.append((it, a, b, c, fa, fb, fc, error))
            if abs(fc) <= tol or error <= tol:
                root = c
                break
            if fa * fc < 0:
                b, fb = c, fc
            else:
                a, fa = c, fc
        if root is None:
            root = (a + b) / 2.0
        return {
            "root": root,
            "f_root": self._eval(root, func),
            "rows": rows,
            "formats": ["d"] + ["float"] * 7,
            "interval": (a, b),
            "original": original,
        }

    def _false_position(self, func, a, b, tol, max_it):
        original = (a, b)
        rows = []
        fa = self._eval(a, func)
        fb = self._eval(b, func)
        if fa == 0.0:
            rows.append((1, a, b, a, fa, fb, fa, 0.0))
            return {
                "root": a,
                "f_root": fa,
                "rows": rows,
                "formats": ["d"] + ["float"] * 7,
                "interval": (a, b),
                "original": original,
            }
        if fb == 0.0:
            rows.append((1, a, b, b, fa, fb, fb, 0.0))
            return {
                "root": b,
                "f_root": fb,
                "rows": rows,
                "formats": ["d"] + ["float"] * 7,
                "interval": (a, b),
                "original": original,
            }
        if fa * fb > 0:
            interval = self._auto_interval(func, a, b)
            if interval is None:
                raise ValueError("La función no cambia de signo en el intervalo dado ni en los rangos sugeridos.")
            a, b = interval
            fa = self._eval(a, func)
            fb = self._eval(b, func)
        prev_c = None
        root = None
        for it in range(1, max_it + 1):
            fa = self._eval(a, func)
            fb = self._eval(b, func)
            if abs(fb - fa) < 1e-14:
                raise ValueError("f(a) y f(b) casi iguales; el método de falsa posición es inestable.")
            c = b - fb * (b - a) / (fb - fa)
            fc = self._eval(c, func)
            ea = abs(fc)
            rows.append((it, a, b, c, fa, fb, fc, ea))
            if abs(fc) <= tol or (prev_c is not None and abs(c - prev_c) <= tol) or abs(b - a) <= tol:
                root = c
                break
            if fa * fc < 0:
                b, fb = c, fc
            else:
                a, fa = c, fc
            prev_c = c
        if root is None:
            root = prev_c if prev_c is not None else (a + b) / 2.0
        return {
            "root": root,
            "f_root": self._eval(root, func),
            "rows": rows,
            "formats": ["d"] + ["float"] * 7,
            "interval": (a, b),
            "original": original,
        }

    def _newton(self, func, x0, tol, max_it):
        rows = []
        x = x0
        for it in range(1, max_it + 1):
            fx = self._eval(x, func)
            dfx = self._derivative(x, func)
            if abs(dfx) < 1e-14:
                raise ValueError("Derivada cercana a cero; intenta con otro punto inicial.")
            x_next = x - fx / dfx
            ea = abs(x_next - x)
            rows.append((it, x, fx, dfx, ea))
            x = x_next
            if ea <= tol or abs(self._eval(x, func)) <= tol:
                break
        return {
            "root": x,
            "f_root": self._eval(x, func),
            "rows": rows,
            "formats": ["d"] + ["float"] * 4,
            "interval": (x, x),
            "original": (x0, None),
        }

    def _secant(self, func, x0, x1, tol, max_it):
        original = (x0, x1)
        rows = []
        a, b = x0, x1
        fa = self._eval(a, func)
        fb = self._eval(b, func)
        if fa == 0.0:
            rows.append((1, a, b, a, fa, 0.0))
            return {
                "root": a,
                "f_root": fa,
                "rows": rows,
                "formats": ["d"] + ["float"] * 5,
                "interval": (a, b),
                "original": original,
            }
        if fb == 0.0:
            rows.append((1, a, b, b, fb, 0.0))
            return {
                "root": b,
                "f_root": fb,
                "rows": rows,
                "formats": ["d"] + ["float"] * 5,
                "interval": (a, b),
                "original": original,
            }
        root = None
        for it in range(1, max_it + 1):
            if abs(fb - fa) < 1e-14:
                raise ValueError("f(x0) y f(x1) casi iguales; el método de la secante falla.")
            c = b - fb * (b - a) / (fb - fa)
            fc = self._eval(c, func)
            ea = abs(c - b)
            rows.append((it, a, b, c, fc, ea))
            if ea <= tol or abs(fc) <= tol:
                root = c
                a, b = b, c
                break
            a, b = b, c
            fa, fb = fb, fc
        if root is None:
            root = b
        return {
            "root": root,
            "f_root": self._eval(root, func),
            "rows": rows,
            "formats": ["d"] + ["float"] * 5,
            "interval": (a, b),
            "original": original,
        }

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

    def _eval(self, x, func):
        return math_utils.evaluate_function(x, func)
    
    def _evaluate_vector(self, xs, func):
        return math_utils.evaluate_function_vectorized(xs, func)
    
    def _derivative(self, x, func, h=1e-6):
        return (self._eval(x + h, func) - self._eval(x - h, func)) / (2.0 * h)
    
    def _plot_function(self, method, func, params, root):
        self.plot_ax.clear()
        try:
            if method in ("Bisección", "Falsa Posición"):
                base_min, base_max = params.get("a", -5.0), params.get("b", 5.0)
            elif method == "Secante":
                base_min = min(params.get("x0", -5.0), params.get("x1", 5.0))
                base_max = max(params.get("x0", -5.0), params.get("x1", 5.0))
            else:
                x0 = params.get("x0", 0.0)
                base_min, base_max = x0 - 5.0, x0 + 5.0
            if base_min == base_max:
                base_min -= 5.0
                base_max += 5.0
            x_min, x_max = self._determine_plot_range(func, base_min, base_max)
            xs = np.linspace(x_min, x_max, 4000)
            ys = self._evaluate_vector(xs, func)
            ys = np.where(np.isfinite(ys), ys, np.nan)
            self.plot_ax.plot(xs, ys, color="#2F80ED", linewidth=2.0, label=f"f(x) = {math_utils.format_function_display(func)}")
            self.plot_ax.axhline(0, color="#666", linestyle="--", linewidth=1.2, alpha=0.7)
            self.plot_ax.axvline(0, color="#666", linestyle="--", linewidth=1.2, alpha=0.7)

            if method in ("Bisección", "Falsa Posición"):
                a_line, b_line = params.get("a"), params.get("b")
                if a_line is not None:
                    self.plot_ax.axvline(a_line, color="#30D158", linestyle=":", linewidth=1.4, label=f"a = {a_line:.3f}")
                    self.plot_ax.plot(a_line, self._eval(a_line, func), "o", color="#30D158", markersize=6)
                if b_line is not None:
                    self.plot_ax.axvline(b_line, color="#FF453A", linestyle=":", linewidth=1.4, label=f"b = {b_line:.3f}")
                    self.plot_ax.plot(b_line, self._eval(b_line, func), "o", color="#FF453A", markersize=6)
                original = params.get("original")
                if isinstance(original, (tuple, list)) and len(original) == 2:
                    oa, ob = original
                    if oa is not None and ob is not None and (oa, ob) != (a_line, b_line):
                        self.plot_ax.axvspan(min(oa, ob), max(oa, ob), color="#FF9F0A", alpha=0.08, label=f"Intervalo original [{oa:.3f}, {ob:.3f}]")
            elif method == "Secante":
                x0, x1 = params.get("x0"), params.get("x1")
                if x0 is not None and x1 is not None:
                    self.plot_ax.scatter([x0, x1], [self._eval(x0, func), self._eval(x1, func)], color="#30D158", marker="o", label="Puntos iniciales")
            elif method == "Newton-Raphson":
                x0 = params.get("x0")
                if x0 is not None:
                    self.plot_ax.plot(x0, self._eval(x0, func), "o", color="#FF9F0A", markersize=7, label=f"x₀ = {x0:.3f}")

            if root is not None and math.isfinite(root):
                fr = self._eval(root, func)
                if math.isfinite(fr):
                    self.plot_ax.plot(root, fr, "o", color="#BB33FF", markersize=9, label=f"Raíz ≈ {root:.4f}")
                    self.plot_ax.axvline(root, color="#BB33FF", linestyle="--", linewidth=1.2, alpha=0.8)

            finite_mask = np.isfinite(ys)
            if np.any(finite_mask):
                dy = np.gradient(np.nan_to_num(ys, nan=0.0), xs)
                vertex_x, vertex_y = [], []
                current = []
                for idx in range(len(xs)):
                    if finite_mask[idx]:
                        current.append(idx)
                    elif current:
                        if len(current) > 1:
                            segment = current
                            deriv = dy[segment]
                            for j in range(1, len(deriv)):
                                if deriv[j - 1] == 0:
                                    continue
                                if deriv[j - 1] > 0 >= deriv[j] or deriv[j - 1] < 0 <= deriv[j]:
                                    k = segment[j]
                                    vertex_x.append(xs[k])
                                    vertex_y.append(ys[k])
                        current = []
                if current and len(current) > 1:
                    deriv = dy[current]
                    for j in range(1, len(deriv)):
                        if deriv[j - 1] == 0:
                            continue
                        if deriv[j - 1] > 0 >= deriv[j] or deriv[j - 1] < 0 <= deriv[j]:
                            k = current[j]
                            vertex_x.append(xs[k])
                            vertex_y.append(ys[k])
                if vertex_x:
                    self.plot_ax.plot(vertex_x, vertex_y, "D", color="#FF9F0A", markersize=6, label="Vértices")

                try:
                    low, high = np.nanpercentile(ys, [1, 99])
                    if np.isfinite(low) and np.isfinite(high) and high > low:
                        pad = 0.1 * (high - low)
                        self.plot_ax.set_ylim(low - pad, high + pad)
                except Exception:
                    pass

            self.plot_ax.set_xlim(x_min, x_max)
            self.plot_ax.set_xlabel("x")
            self.plot_ax.set_ylabel("f(x)")
            self.plot_ax.grid(True, linestyle="--", alpha=0.35)
            self.plot_ax.legend()
        except Exception as err:
            self._show_error_dialog(str(err))
            self.plot_ax.clear()
            self.plot_ax.text(0.5, 0.5, f"No se pudo graficar:\n{err}", ha="center", va="center", color="#FF453A")
            self.plot_ax.set_axis_off()
        self.figure.tight_layout()
        self.canvas.draw_idle()
    def _show_error_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error al graficar")
        dlg.setText(message)
        dlg.exec()

    def _auto_interval(self, func, a, b):
        res = self._suggest_interval_core(func)
        if res is None:
            return None
        return res[0], res[1]

    def _suggest_interval_core(self, func, prefer_zero=True):
        search_specs = [(-10, 10, 0.1), (-50, 50, 0.2), (-100, 100, 0.5)]
        intervals = []
        zeros = []
        for start, end, step in search_specs:
            prev_x = prev_y = None
            x = float(start)
            while x <= end:
                try:
                    y = self._eval(x, func)
                except Exception:
                    prev_x = prev_y = None
                    x = round(x + step, 10)
                    continue
                if not math.isfinite(y):
                    prev_x = prev_y = None
                    x = round(x + step, 10)
                    continue
                if abs(y) < 1e-12:
                    zeros.append((x, step))
                if prev_y is not None and math.isfinite(prev_y) and prev_y * y < 0:
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
        best = sorted(intervals, key=lambda ab: (abs(sum(ab) / 2.0), abs(ab[1] - ab[0])))[0]
        return best[0], best[1], intervals, zeros

    def _determine_plot_range(self, func, base_min, base_max):
        try:
            res = self._suggest_interval_core(func, prefer_zero=False)
            if res:
                a, b, intervals, _ = res
                xs = [a, b]
                for ia, ib in intervals:
                    xs.extend([ia, ib])
                x_min = min(xs) - 2.0
                x_max = max(xs) + 2.0
            else:
                x_min, x_max = base_min, base_max
            if x_max - x_min < 10.0:
                mid = (x_min + x_max) / 2.0
                x_min, x_max = mid - 5.0, mid + 5.0
            return max(-100.0, x_min), min(100.0, x_max)
        except Exception:
            return base_min - 2.0, base_max + 2.0

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

    def _to_mathtext(self, s: str) -> str:
        expr = math_utils.format_function_display(s)
        return self._normalize_exponents(expr)

    def _normalize_exponents(self, expr: str) -> str:
        out = []
        i = 0
        n = len(expr)
        special_tokens = {
            "x²": "x^(2)",
            "x³": "x^(3)",
            "^": "^(",
            "e": "e",
            "e^x": "e^(",
        }
        while i < n:
            ch = expr[i]
            if ch == "^" and i + 1 < n:
                i += 1
                if expr[i] == "(":
                    depth = 1
                    start = i + 1
                    j = start
                    while j < n and depth:
                        if expr[j] == "(":
                            depth += 1
                        elif expr[j] == ")":
                            depth -= 1
                        j += 1
                    out.append("^{")
                    out.append(expr[start:j - 1])
                    out.append("}")
                    i = j
                else:
                    start = i
                    while start < n and (expr[start].isalnum() or expr[start] in "._πe"):
                        start += 1
                    out.append("^{")
                    out.append(expr[i:start])
                    out.append("}")
                    i = start
            else:
                out.append(ch)
                i += 1
        return "".join(out)

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
            for idx, (zx, step) in enumerate(sorted(zeros, key=lambda z: abs(z[0]))):
                report.append(f"{idx+1}. {zx:.6f} (paso {step:.1e})")
        self.log.appendPlainText("\n".join(report))

    def _clear(self):
        self.func.clear()
        self.log.clear()
        self.plot_ax.clear()
        self.plot_ax.set_axis_off()
        self.canvas.draw_idle()
        self.last_root = None
        self.last_func = ""
        self.last_params = {}
        self._set_method("Bisección")

    def _eval(self, x, func):
        return math_utils.evaluate_function(x, func)
    
    def _evaluate_vector(self, xs, func):
        return math_utils.evaluate_function_vectorized(xs, func)
    
    def _derivative(self, x, func, h=1e-6):
        return (self._eval(x + h, func) - self._eval(x - h, func)) / (2.0 * h)
    
    def _plot_function(self, method, func, params, root):
        self.plot_ax.clear()
        try:
            if method in ("Bisección", "Falsa Posición"):
                base_min, base_max = params.get("a", -5.0), params.get("b", 5.0)
            elif method == "Secante":
                base_min = min(params.get("x0", -5.0), params.get("x1", 5.0))
                base_max = max(params.get("x0", -5.0), params.get("x1", 5.0))
            else:
                x0 = params.get("x0", 0.0)
                base_min, base_max = x0 - 5.0, x0 + 5.0
            if base_min == base_max:
                base_min -= 5.0
                base_max += 5.0
            x_min, x_max = self._determine_plot_range(func, base_min, base_max)
            xs = np.linspace(x_min, x_max, 4000)
            ys = self._evaluate_vector(xs, func)
            ys = np.where(np.isfinite(ys), ys, np.nan)
            self.plot_ax.plot(xs, ys, color="#2F80ED", linewidth=2.0, label=f"f(x) = {math_utils.format_function_display(func)}")
            self.plot_ax.axhline(0, color="#666", linestyle="--", linewidth=1.2, alpha=0.7)
            self.plot_ax.axvline(0, color="#666", linestyle="--", linewidth=1.2, alpha=0.7)

            if method in ("Bisección", "Falsa Posición"):
                a_line, b_line = params.get("a"), params.get("b")
                if a_line is not None:
                    self.plot_ax.axvline(a_line, color="#30D158", linestyle=":", linewidth=1.4, label=f"a = {a_line:.3f}")
                    self.plot_ax.plot(a_line, self._eval(a_line, func), "o", color="#30D158", markersize=6)
                if b_line is not None:
                    self.plot_ax.axvline(b_line, color="#FF453A", linestyle=":", linewidth=1.4, label=f"b = {b_line:.3f}")
                    self.plot_ax.plot(b_line, self._eval(b_line, func), "o", color="#FF453A", markersize=6)
                original = params.get("original")
                if isinstance(original, (tuple, list)) and len(original) == 2:
                    oa, ob = original
                    if oa is not None and ob is not None and (oa, ob) != (a_line, b_line):
                        self.plot_ax.axvspan(min(oa, ob), max(oa, ob), color="#FF9F0A", alpha=0.08, label=f"Intervalo original [{oa:.3f}, {ob:.3f}]")
            elif method == "Secante":
                x0, x1 = params.get("x0"), params.get("x1")
                if x0 is not None and x1 is not None:
                    self.plot_ax.scatter([x0, x1], [self._eval(x0, func), self._eval(x1, func)], color="#30D158", marker="o", label="Puntos iniciales")
            elif method == "Newton-Raphson":
                x0 = params.get("x0")
                if x0 is not None:
                    self.plot_ax.plot(x0, self._eval(x0, func), "o", color="#FF9F0A", markersize=7, label=f"x₀ = {x0:.3f}")

            if root is not None and math.isfinite(root):
                fr = self._eval(root, func)
                if math.isfinite(fr):
                    self.plot_ax.plot(root, fr, "o", color="#BB33FF", markersize=9, label=f"Raíz ≈ {root:.4f}")
                    self.plot_ax.axvline(root, color="#BB33FF", linestyle="--", linewidth=1.2, alpha=0.8)

            finite_mask = np.isfinite(ys)
            if np.any(finite_mask):
                dy = np.gradient(np.nan_to_num(ys, nan=0.0), xs)
                vertex_x, vertex_y = [], []
                current = []
                for idx in range(len(xs)):
                    if finite_mask[idx]:
                        current.append(idx)
                    elif current:
                        if len(current) > 1:
                            segment = current
                            deriv = dy[segment]
                            for j in range(1, len(deriv)):
                                if deriv[j - 1] == 0:
                                    continue
                                if deriv[j - 1] > 0 >= deriv[j] or deriv[j - 1] < 0 <= deriv[j]:
                                    k = segment[j]
                                    vertex_x.append(xs[k])
                                    vertex_y.append(ys[k])
                        current = []
                if current and len(current) > 1:
                    deriv = dy[current]
                    for j in range(1, len(deriv)):
                        if deriv[j - 1] == 0:
                            continue
                        if deriv[j - 1] > 0 >= deriv[j] or deriv[j - 1] < 0 <= deriv[j]:
                            k = current[j]
                            vertex_x.append(xs[k])
                            vertex_y.append(ys[k])
                if vertex_x:
                    self.plot_ax.plot(vertex_x, vertex_y, "D", color="#FF9F0A", markersize=6, label="Vértices")

                try:
                    low, high = np.nanpercentile(ys, [1, 99])
                    if np.isfinite(low) and np.isfinite(high) and high > low:
                        pad = 0.1 * (high - low)
                        self.plot_ax.set_ylim(low - pad, high + pad)
                except Exception:
                    pass

            self.plot_ax.set_xlim(x_min, x_max)
            self.plot_ax.set_xlabel("x")
            self.plot_ax.set_ylabel("f(x)")
            self.plot_ax.grid(True, linestyle="--", alpha=0.35)
            self.plot_ax.legend()
        except Exception as err:
            self._show_error_dialog(str(err))
            self.plot_ax.clear()
            self.plot_ax.text(0.5, 0.5, f"No se pudo graficar:\n{err}", ha="center", va="center", color="#FF453A")
            self.plot_ax.set_axis_off()
        self.figure.tight_layout()
        self.canvas.draw_idle()
    def _show_error_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error al graficar")
        dlg.setText(message)
        dlg.exec()

    def _auto_interval(self, func, a, b):
        res = self._suggest_interval_core(func)
        if res is None:
            return None
        return res[0], res[1]

    def _suggest_interval_core(self, func, prefer_zero=True):
        search_specs = [(-10, 10, 0.1), (-50, 50, 0.2), (-100, 100, 0.5)]
        intervals = []
        zeros = []
        for start, end, step in search_specs:
            prev_x = prev_y = None
            x = float(start)
            while x <= end:
                try:
                    y = self._eval(x, func)
                except Exception:
                    prev_x = prev_y = None
                    x = round(x + step, 10)
                    continue
                if not math.isfinite(y):
                    prev_x = prev_y = None
                    x = round(x + step, 10)
                    continue
                if abs(y) < 1e-12:
                    zeros.append((x, step))
                if prev_y is not None and math.isfinite(prev_y) and prev_y * y < 0:
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
        best = sorted(intervals, key=lambda ab: (abs(sum(ab) / 2.0), abs(ab[1] - ab[0])))[0]
        return best[0], best[1], intervals, zeros

    def _determine_plot_range(self, func, base_min, base_max):
        try:
            res = self._suggest_interval_core(func, prefer_zero=False)
            if res:
                a, b, intervals, _ = res
                xs = [a, b]
                for ia, ib in intervals:
                    xs.extend([ia, ib])
                x_min = min(xs) - 2.0
                x_max = max(xs) + 2.0
            else:
                x_min, x_max = base_min, base_max
            if x_max - x_min < 10.0:
                mid = (x_min + x_max) / 2.0
                x_min, x_max = mid - 5.0, mid + 5.0
            return max(-100.0, x_min), min(100.0, x_max)
        except Exception:
            return base_min - 2.0, base_max + 2.0

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

    def _to_mathtext(self, s: str) -> str:
        expr = math_utils.format_function_display(s)
        return self._normalize_exponents(expr)

    def _normalize_exponents(self, expr: str) -> str:
        out = []
        i = 0
        n = len(expr)
        special_tokens = {
            "x²": "x^(2)",
            "x³": "x^(3)",
            "^": "^(",
            "e": "e",
            "e^x": "e^(",
        }
        while i < n:
            ch = expr[i]
            if ch == "^" and i + 1 < n:
                i += 1
                if expr[i] == "(":
                    depth = 1
                    start = i + 1
                    j = start
                    while j < n and depth:
                        if expr[j] == "(":
                            depth += 1
                        elif expr[j] == ")":
                            depth -= 1
                        j += 1
                    out.append("^{")
                    out.append(expr[start:j - 1])
                    out.append("}")
                    i = j
                else:
                    start = i
                    while start < n and (expr[start].isalnum() or expr[start] in "._πe"):
                        start += 1
                    out.append("^{")
                    out.append(expr[i:start])
                    out.append("}")
                    i = start
            else:
                out.append(ch)
                i += 1
        return "".join(out)

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
            for idx, (zx, step) in enumerate(sorted(zeros, key=lambda z: abs(z[0]))):
                report.append(f"{idx+1}. {zx:.6f} (paso {step:.1e})")
        self.log.appendPlainText("\n".join(report))

    def _clear(self):
        self.func.clear()
        self.log.clear()
        self.plot_ax.clear()
        self.plot_ax.set_axis_off()
        self.canvas.draw_idle()
        self.last_root = None
        self.last_func = ""
        self.last_params = {}
        self._set_method("Bisección")

    def _eval(self, x, func):
        return math_utils.evaluate_function(x, func)
    
    def _evaluate_vector(self, xs, func):
        return math_utils.evaluate_function_vectorized(xs, func)
    
    def _derivative(self, x, func, h=1e-6):
        return (self._eval(x + h, func) - self._eval(x - h, func)) / (2.0 * h)
    
    def _plot_function(self, method, func, params, root):
        self.plot_ax.clear()
        try:
            if method in ("Bisección", "Falsa Posición"):
                base_min, base_max = params.get("a", -5.0), params.get("b", 5.0)
            elif method == "Secante":
                base_min = min(params.get("x0", -5.0), params.get("x1", 5.0))
                base_max = max(params.get("x0", -5.0), params.get("x1", 5.0))
            else:
                x0 = params.get("x0", 0.0)
                base_min, base_max = x0 - 5.0, x0 + 5.0
            if base_min == base_max:
                base_min -= 5.0
                base_max += 5.0
            x_min, x_max = self._determine_plot_range(func, base_min, base_max)
            xs = np.linspace(x_min, x_max, 4000)
            ys = self._evaluate_vector(xs, func)
            ys = np.where(np.isfinite(ys), ys, np.nan)
            self.plot_ax.plot(xs, ys, color="#2F80ED", linewidth=2.0, label=f"f(x) = {math_utils.format_function_display(func)}")
            self.plot_ax.axhline(0, color="#666", linestyle="--", linewidth=1.2, alpha=0.7)
            self.plot_ax.axvline(0, color="#666", linestyle="--", linewidth=1.2, alpha=0.7)

            if method in ("Bisección", "Falsa Posición"):
                a_line, b_line = params.get("a"), params.get("b")
                if a_line is not None:
                    self.plot_ax.axvline(a_line, color="#30D158", linestyle=":", linewidth=1.4, label=f"a = {a_line:.3f}")
                    self.plot_ax.plot(a_line, self._eval(a_line, func), "o", color="#30D158", markersize=6)
                if b_line is not None:
                    self.plot_ax.axvline(b_line, color="#FF453A", linestyle=":", linewidth=1.4, label=f"b = {b_line:.3f}")
                    self.plot_ax.plot(b_line, self._eval(b_line, func), "o", color="#FF453A", markersize=6)
                original = params.get("original")
                if isinstance(original, (tuple, list)) and len(original) == 2:
                    oa, ob = original
                    if oa is not None and ob is not None and (oa, ob) != (a_line, b_line):
                        self.plot_ax.axvspan(min(oa, ob), max(oa, ob), color="#FF9F0A", alpha=0.08, label=f"Intervalo original [{oa:.3f}, {ob:.3f}]")
            elif method == "Secante":
                x0, x1 = params.get("x0"), params.get("x1")
                if x0 is not None and x1 is not None:
                    self.plot_ax.scatter([x0, x1], [self._eval(x0, func), self._eval(x1, func)], color="#30D158", marker="o", label="Puntos iniciales")
            elif method == "Newton-Raphson":
                x0 = params.get("x0")
                if x0 is not None:
                    self.plot_ax.plot(x0, self._eval(x0, func), "o", color="#FF9F0A", markersize=7, label=f"x₀ = {x0:.3f}")

            if root is not None and math.isfinite(root):
                fr = self._eval(root, func)
                if math.isfinite(fr):
                    self.plot_ax.plot(root, fr, "o", color="#BB33FF", markersize=9, label=f"Raíz ≈ {root:.4f}")
                    self.plot_ax.axvline(root, color="#BB33FF", linestyle="--", linewidth=1.2, alpha=0.8)

            finite_mask = np.isfinite(ys)
            if np.any(finite_mask):
                dy = np.gradient(np.nan_to_num(ys, nan=0.0), xs)
                vertex_x, vertex_y = [], []
                current = []
                for idx in range(len(xs)):
                    if finite_mask[idx]:
                        current.append(idx)
                    elif current:
                        if len(current) > 1:
                            segment = current
                            deriv = dy[segment]
                            for j in range(1, len(deriv)):
                                if deriv[j - 1] == 0:
                                    continue
                                if deriv[j - 1] > 0 >= deriv[j] or deriv[j - 1] < 0 <= deriv[j]:
                                    k = segment[j]
                                    vertex_x.append(xs[k])
                                    vertex_y.append(ys[k])
                        current = []
                if current and len(current) > 1:
                    deriv = dy[current]
                    for j in range(1, len(deriv)):
                        if deriv[j - 1] == 0:
                            continue
                        if deriv[j - 1] > 0 >= deriv[j] or deriv[j - 1] < 0 <= deriv[j]:
                            k = current[j]
                            vertex_x.append(xs[k])
                            vertex_y.append(ys[k])
                if vertex_x:
                    self.plot_ax.plot(vertex_x, vertex_y, "D", color="#FF9F0A", markersize=6, label="Vértices")

                try:
                    low, high = np.nanpercentile(ys, [1, 99])
                    if np.isfinite(low) and np.isfinite(high) and high > low:
                        pad = 0.1 * (high - low)
                        self.plot_ax.set_ylim(low - pad, high + pad)
                except Exception:
                    pass

            self.plot_ax.set_xlim(x_min, x_max)
            self.plot_ax.set_xlabel("x")
            self.plot_ax.set_ylabel("f(x)")
            self.plot_ax.grid(True, linestyle="--", alpha=0.35)
            self.plot_ax.legend()
        except Exception as err:
            self._show_error_dialog(str(err))
            self.plot_ax.clear()
            self.plot_ax.text(0.5, 0.5, f"No se pudo graficar:\n{err}", ha="center", va="center", color="#FF453A")
            self.plot_ax.set_axis_off()
        self.figure.tight_layout()
        self.canvas.draw_idle()
    def _show_error_dialog(self, message):
        dlg = QMessageBox(self)
        dlg.setIcon(QMessageBox.Critical)
        dlg.setWindowTitle("Error al graficar")
        dlg.setText(message)
        dlg.exec()

    def _auto_interval(self, func, a, b):
        res = self._suggest_interval_core(func)
        if res is None:
            return None
        return res[0], res[1]

    def _suggest_interval_core(self, func, prefer_zero=True):
        search_specs = [(-10, 10, 0.1), (-50, 50, 0.2), (-100, 100, 0.5)]
        intervals = []
        zeros = []
        for start, end, step in search_specs:
            prev_x = prev_y = None
            x = float(start)
            while x <= end:
                try:
                    y = self._eval(x, func)
                except Exception:
                    prev_x = prev_y = None
                    x = round(x + step, 10)
                    continue
                if not math.isfinite(y):
                    prev_x = prev_y = None
                    x = round(x + step, 10)
                    continue
                if abs(y) < 1e-12:
                    zeros.append((x, step))
                if prev_y is not None and math.isfinite(prev_y) and prev_y * y < 0:
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
        best = sorted(intervals, key=lambda ab: (abs(sum(ab) / 2.0), abs(ab[1] - ab[0])))[0]
        return best[0], best[1], intervals, zeros

    def _determine_plot_range(self, func, base_min, base_max):
        try:
            res = self._suggest_interval_core(func, prefer_zero=False)
            if res:
                a, b, intervals, _ = res
                xs = [a, b]
                for ia, ib in intervals:
                    xs.extend([ia, ib])
                x_min = min(xs) - 2.0
                x_max = max(xs) + 2.0
            else:
                x_min, x_max = base_min, base_max
            if x_max - x_min < 10.0:
                mid = (x_min + x_max) / 2.0
                x_min, x_max = mid - 5.0, mid + 5.0
            return max(-100.0, x_min), min(100.0, x_max)
        except Exception:
            return base_min - 2.0, base_max + 2.0

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

    def _to_mathtext(self, s: str) -> str:
        expr = math_utils.format_function_display(s)
        return self._normalize_exponents(expr)

    def _normalize_exponents(self, expr: str) -> str:
        out = []
        i = 0
        n = len(expr)
        special_tokens = {
            "x²": "x^(2)",
            "x³": "x^(3)",
            "^": "^(",
            "e": "e",
            "e^x": "e^(",
        }
        while i < n:
            ch = expr[i]
            if ch == "^" and i + 1 < n:
                i += 1
                if expr[i] == "(":
                    depth = 1
                    start = i + 1
                    j = start
                    while j < n and depth:
                        if expr[j] == "(":
                            depth += 1
                        elif expr[j] == ")":
                            depth -= 1
                        j += 1
                    out.append("^{")
                    out.append(expr[start:j - 1])
                    out.append("}")
                    i = j
                else:
                    start = i
                    while start < n and (expr[start].isalnum() or expr[start] in "._πe"):
                        start += 1
                    out.append("^{")
                    out.append(expr[i:start])
                    out.append("}")
                    i = start
            else:
                out.append(ch)
                i += 1
        return "".join(out)

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
            for idx, (zx, step) in enumerate(sorted(zeros, key=lambda z: abs(z[0]))):
                report.append(f"{idx+1}. {zx:.6f} (paso {step:.1e})")
        self.log.appendPlainText("\n".join(report))

    def _clear(self):
        self.func.clear()
        self.log.clear()
        self.plot_ax.clear()
        self.plot_ax.set_axis_off()
        self.canvas.draw_idle()
        self.last_root = None
        self.last_func = ""
        self.last_params = {}
        self._set_method("Bisección")

class MainWindow(QMainWindow):
    def __init__(self, parent=None, colors=None):
        super().__init__(parent)
        self.colors = colors or DEFAULT_COLORS
        self.setWindowTitle("Calculadora de Álgebra")
        self.resize(1280, 840)

        tabs = QTabWidget()
        tabs.addTab(MatricesPage(self.colors, self), "Matrices")
        tabs.addTab(GaussJordanPage(self.colors, self), "Gauss-Jordan")
        tabs.addTab(RootFindingPage(self.colors, self), "Raíces")

        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
