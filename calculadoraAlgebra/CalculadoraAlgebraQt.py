import sys
from PySide6 import QtGui
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QPlainTextEdit, QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QAbstractScrollArea, QScrollArea, QSlider, QSizePolicy, QButtonGroup, QMessageBox, QAbstractSpinBox, QDialog, QDialogButtonBox
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

        # Tab 2: Procedimiento
        self.tab_steps = QWidget(); steps_container_layout = QVBoxLayout(self.tab_steps); steps_container_layout.setContentsMargins(8,8,8,8); steps_container_layout.setAlignment(Qt.AlignTop)
        self.scroll_area = QScrollArea(); self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_container = QWidget(); self.steps_layout = QVBoxLayout(scroll_container)
        self.steps_layout.setContentsMargins(8, 8, 8, 8); self.steps_layout.setSpacing(10); self.steps_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(scroll_container)
        steps_container_layout.addWidget(self.scroll_area)
        self.inner_tabs.addTab(self.tab_steps, "Procedimiento")

        # Resultado Final se muestra dentro de Procedimiento; se elimina pestaña dedicada

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
        # insertar al final del scroll de Procedimiento, antes del stretch
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
            rows, cols = base.shape
            partial = Matrix([[base[i, j] for j in range(cols)] for i in range(rows)])
            for i in range(rows):
                for j in range(cols):
                    old = partial[i, j]
                    new = base[i, j] * coef
                    partial[i, j] = new
                    self._add_step_panel(
                        f"Paso {self._next_step}",
                        f"c[{i+1},{j+1}] = ({var})[{i+1},{j+1}] · {self._fmt(coef)} = {self._fmt(new)}",
                        partial
                    ); self._next_step += 1
            scaled = partial
            return scaled, idx
        def read_term(idx):
            mat, idx = read_factor(idx)
            while idx < len(tokens) and tokens[idx] == '*':
                idx += 1
                right, idx = read_factor(idx)
                rowsA, colsA = mat.shape; rowsB, colsB = right.shape
                if colsA != rowsB:
                    raise ValueError("Dimensiones no compatibles para multiplicación")
                res = clone_zero(rowsA, colsB)
                for i in range(rowsA):
                    for j in range(colsB):
                        terms = []
                        s = Fraction(0)
                        for k in range(colsA):
                            prod = mat[i, k] * right[k, j]
                            s += prod
                            terms.append(f"{self._fmt(mat[i,k])}×{self._fmt(right[k,j])}")
                        res[i, j] = s
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"c[{i+1},{j+1}] = " + " + ".join(terms) + f" = {self._fmt(s)}",
                            res
                        ); self._next_step += 1
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
                        old = term[r, c]
                        new = old * Fraction(-1)
                        term[r, c] = new
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"c[{r+1},{c+1}] = (−1)×{self._fmt(old)} = {self._fmt(new)}",
                            term
                        ); self._next_step += 1
            prev = result
            result = term if result is None else self._matrix_add(result, term)
            if prev is not None:
                rows, cols = result.shape
                for r in range(rows):
                    for c in range(cols):
                        old = prev[r, c]
                        add = term[r, c]
                        val = old + add
                        prev[r, c] = val
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"acum[{r+1},{c+1}] = {self._fmt(old)} + {self._fmt(add)} = {self._fmt(val)}",
                            prev
                        ); self._next_step += 1
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
            # Si el modo es "Expresión" pero no hay expresión, por defecto mostrar procedimiento de Suma
            if basic == "Expresión":
                basic = "Suma"
            adv = self.adv_op.currentText()
            base = matA
            if basic == "Suma":
                res = Matrix([[matA[i, j] for j in range(matA.cols)] for i in range(matA.rows)])
                for i in range(matA.rows):
                    for j in range(matA.cols):
                        old = res[i, j]
                        val = matA[i, j] + matB[i, j]
                        res[i, j] = val
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"c[{i+1},{j+1}] = A[{i+1},{j+1}] + B[{i+1},{j+1}] = {self._fmt(val)}",
                            res
                        ); self._next_step += 1
            elif basic == "Resta":
                res = Matrix([[matA[i, j] for j in range(matA.cols)] for i in range(matA.rows)])
                for i in range(matA.rows):
                    for j in range(matA.cols):
                        old = res[i, j]
                        val = matA[i, j] - matB[i, j]
                        res[i, j] = val
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"c[{i+1},{j+1}] = A[{i+1},{j+1}] − B[{i+1},{j+1}] = {self._fmt(val)}",
                            res
                        ); self._next_step += 1
            elif basic == "Multiplicación":
                res = Matrix([[Fraction(0) for _ in range(matB.cols)] for _ in range(matA.rows)])
                for i in range(matA.rows):
                    for j in range(matB.cols):
                        terms = []
                        s = Fraction(0)
                        for k in range(matA.cols):
                            prod = matA[i, k] * matB[k, j]
                            s += prod
                            terms.append(f"{self._fmt(matA[i,k])}×{self._fmt(matB[k,j])}")
                        res[i, j] = s
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"c[{i+1},{j+1}] = " + " + ".join(terms) + f" = {self._fmt(s)}",
                            res
                        ); self._next_step += 1
            elif basic == "Escalar":
                k = parse_fraction(self.scalar_input.text() or "1")
                res = Matrix([[base[i, j] for j in range(base.cols)] for i in range(base.rows)])
                for i in range(base.rows):
                    for j in range(base.cols):
                        old = res[i, j]
                        val = base[i, j] * k
                        res[i, j] = val
                        self._add_step_panel(
                            f"Paso {self._next_step}",
                            f"c[{i+1},{j+1}] = A[{i+1},{j+1}] · {self._fmt(k)} = {self._fmt(val)}",
                            res
                        ); self._next_step += 1
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
        main = QVBoxLayout(self); main.setContentsMargins(24,24,24,24); main.setSpacing(16)
        title = QLabel("Sistema de ecuaciones lineales")
        title.setStyleSheet(f"color:{colors['accent']};"); title.setFont(QtGui.QFont("Segoe UI", 22, QtGui.QFont.Bold))
        main.addWidget(title, alignment=Qt.AlignLeft)

        controls_top = QHBoxLayout();
        self.spin_rows = QSpinBox(); self.spin_rows.setRange(1, 10); self.spin_rows.setValue(3)
        self.spin_cols = QSpinBox(); self.spin_cols.setRange(1, 10); self.spin_cols.setValue(3)
        controls_top.addWidget(QLabel("Ecuaciones:")); controls_top.addWidget(self.spin_rows)
        controls_top.addWidget(QLabel("Variables:")); controls_top.addWidget(self.spin_cols)
        controls_top.addStretch(1)
        main.addLayout(controls_top)

        actions = QHBoxLayout(); actions.addStretch(1)
        self.btn_generate = QPushButton("Generar matriz aumentada")
        self.btn_equations = QPushButton("Ingresar ecuaciones…")
        self.method_combo = QComboBox(); self.method_combo.addItems(["Gauss‑Jordan", "Gauss", "Cramer", "Sarrus"]); self.method_combo.setFixedWidth(180)
        self.btn_solve = QPushButton("Resolver"); self.btn_clear = QPushButton("Limpiar")
        for w in (self.btn_generate, self.btn_equations, self.method_combo, self.btn_solve, self.btn_clear):
            actions.addWidget(w)
        main.addLayout(actions)

        layout_main = QHBoxLayout()
        left_col = QVBoxLayout(); left_col.setSpacing(10)
        self.table = QTableWidget(3, 4)
        self.table.verticalHeader().setVisible(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        for c in range(self.table.columnCount()):
            self.table.setColumnWidth(c, 100)
        left_col.addWidget(self.table)

        lbl_det = QLabel("Procedimiento detallado"); lbl_det.setStyleSheet(f"color:{self.colors['text']};")
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(280); self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        left_col.addWidget(lbl_det)
        left_col.addWidget(self.log)

        self.result_card = QFrame(); self.result_card.setObjectName("resultCard")
        self.result_card.setStyleSheet(
            f"""
            QFrame#resultCard {{
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 14px;
            }}
            QLabel#resultTitle {{ color: {self.colors['accent']}; font-size: 18px; font-weight: 700; }}
            QLabel#resultLabel {{ color: {self.colors['text_secondary']}; }}
            """
        )
        card_lay = QVBoxLayout(self.result_card); card_lay.setContentsMargins(16,16,16,16); card_lay.setSpacing(8)
        self.res_title = QLabel("Resultado"); self.res_title.setObjectName("resultTitle")
        card_lay.addWidget(self.res_title)
        self.res_status = QLabel("") ; self.res_status.setObjectName("resultLabel")
        self.res_pivots = QLabel(""); self.res_pivots.setObjectName("resultLabel")
        self.res_free = QLabel(""); self.res_free.setObjectName("resultLabel")
        self.res_indep = QLabel(""); self.res_indep.setObjectName("resultLabel")
        card_lay.addWidget(self.res_status)
        card_lay.addWidget(self.res_pivots)
        card_lay.addWidget(self.res_free)
        card_lay.addWidget(self.res_indep)
        self.res_vars = QTableWidget(0, 2)
        self.res_vars.setHorizontalHeaderLabels(["Variable", "Valor"])
        self.res_vars.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.res_vars.verticalHeader().setVisible(False)
        self.res_vars.setMinimumHeight(180)
        card_lay.addWidget(self.res_vars)

        layout_main.addLayout(left_col, 3)
        layout_main.addWidget(self.result_card, 2)
        main.addLayout(layout_main)

        self.btn_generate.clicked.connect(self.generate_matrix)
        self.btn_solve.clicked.connect(self.solve)
        self.btn_clear.clicked.connect(self.clear)
        self.btn_equations.clicked.connect(self.open_equations_dialog)
        self.setStyleSheet(f"QLabel {{ color:{self.colors['text']}; }} QTableWidget {{ background:{self.colors['matrix_bg']}; color:{self.colors['text']}; }} QPlainTextEdit {{ background:{self.colors['secondary_bg']}; color:{self.colors['text']}; }}")

        self.generate_matrix()

    def generate_matrix(self):
        rows = self.spin_rows.value(); cols = self.spin_cols.value()
        self.table.setRowCount(rows); self.table.setColumnCount(cols + 1)
        for c in range(self.table.columnCount()):
            self.table.setColumnWidth(c, 100)
        for r in range(rows):
            for c in range(cols + 1):
                self.table.setItem(r, c, QTableWidgetItem("0"))
        self._set_headers(rows, cols)

    def solve(self):
        rows = self.table.rowCount(); cols = self.table.columnCount(); data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                item = self.table.item(r, c); text = item.text() if item else "0"
                row.append(parse_fraction(text))
            data.append(row)
        self.log.clear()
        method = self.method_combo.currentText()
        try:
            if method == "Gauss‑Jordan":
                mat = [row[:] for row in data]
                n = len(mat); m = len(mat[0]); n_vars = m - 1
                pivot_cols = []
                r = 0
                self.log.appendPlainText("Inicio: matriz aumentada")
                self.log.appendPlainText(self._format_matrix_lines(mat))
                for c in range(n_vars):
                    piv = None
                    for i in range(r, n):
                        if mat[i][c] != 0:
                            piv = i; break
                    if piv is None:
                        self.log.appendPlainText(f"Columna {c+1} sin pivote. Variable libre x{c+1}")
                        continue
                    self.log.appendPlainText(f"Seleccionar pivote en columna {c+1}: fila {piv+1}")
                    if piv != r:
                        mat[r], mat[piv] = mat[piv], mat[r]
                        self.log.appendPlainText(f"Intercambiar fila {r+1} con {piv+1}")
                        self.log.appendPlainText(self._format_matrix_lines(mat))
                    pivot = mat[r][c]
                    if pivot != 1:
                        for j in range(c, m):
                            mat[r][j] = mat[r][j] / pivot
                        self.log.appendPlainText(f"Dividir fila {r+1} por {pivot}")
                        self.log.appendPlainText(self._format_matrix_lines(mat))
                    for i in range(n):
                        if i != r and mat[i][c] != 0:
                            factor = mat[i][c]
                            for j in range(c, m):
                                mat[i][j] -= factor * mat[r][j]
                            self.log.appendPlainText(f"R{i+1} = R{i+1} - {factor} * R{r+1}")
                            self.log.appendPlainText(self._format_matrix_lines(mat))
                    pivot_cols.append(c)
                    r += 1
                    if r == n:
                        break
                inconsistent = False
                for i in range(n):
                    if all(mat[i][j] == 0 for j in range(n_vars)) and mat[i][-1] != 0:
                        inconsistent = True
                        break
                self.log.appendPlainText("")
                self.log.appendPlainText("Análisis del sistema:")
                self.log.appendPlainText(f"Columnas pivote: {[p+1 for p in pivot_cols]}")
                free_vars = [i+1 for i in range(n_vars) if i not in pivot_cols]
                if inconsistent:
                    self.log.appendPlainText("El sistema es INCONSISTENTE (no tiene solución)")
                elif len(pivot_cols) < n_vars:
                    self.log.appendPlainText("El sistema tiene INFINITAS SOLUCIONES (variables libres)")
                    self.log.appendPlainText(f"Variables libres: x{', x'.join(map(str, free_vars))}" if free_vars else "")
                else:
                    self.log.appendPlainText("El sistema tiene SOLUCIÓN ÚNICA")
                rankA = len(pivot_cols)
                lin_indep = "INDEPENDIENTE" if rankA == n_vars else "DEPENDIENTE"
                self.log.appendPlainText(f"Columnas de A: {lin_indep}")
                sol = None
                if not inconsistent and len(pivot_cols) == n_vars:
                    sol = [Fraction(0)] * n_vars
                    for c in range(n_vars):
                        row_idx = None
                        for i in range(n):
                            if mat[i][c] == 1 and all(mat[i][k] == 0 for k in range(n_vars) if k != c):
                                row_idx = i; break
                        val = mat[row_idx][-1] if row_idx is not None else Fraction(0)
                        sol[c] = val
                    self.log.appendPlainText("")
                    self.log.appendPlainText("Valores de variables:")
                    for i, val in enumerate(sol, start=1):
                        self.log.appendPlainText(f"x{i} = {self._fmt_val(val)}")
                status_txt = "INCONSISTENTE" if inconsistent else ("INFINITAS" if len(pivot_cols) < n_vars else "ÚNICA")
                self._update_result_panel(status_txt, pivot_cols, free_vars, lin_indep, sol)
            elif method == "Gauss":
                mat = [row[:] for row in data]
                n = len(mat); m = len(mat[0])
                n_vars = m - 1
                self.log.appendPlainText("Inicio: matriz aumentada")
                self.log.appendPlainText(self._format_matrix_lines(mat))
                pivot_cols = []
                for i in range(n_vars):
                    piv = None
                    for r in range(i, n):
                        if mat[r][i] != 0:
                            piv = r; break
                    if piv is None:
                        self.log.appendPlainText(f"Columna {i+1} sin pivote. Variable libre x{i+1}")
                        continue
                    pivot_cols.append(i)
                    if piv != i:
                        mat[i], mat[piv] = mat[piv], mat[i]
                        self.log.appendPlainText(f"Intercambiar fila {i+1} con {piv+1}")
                        self.log.appendPlainText(self._format_matrix_lines(mat))
                    pivot = mat[i][i]
                    for r in range(i+1, n):
                        if mat[r][i] != 0:
                            factor = mat[r][i] / pivot
                            for c in range(i, m):
                                mat[r][c] -= factor * mat[i][c]
                            self.log.appendPlainText(f"R{r+1} = R{r+1} - {factor} * R{i+1}")
                            self.log.appendPlainText(self._format_matrix_lines(mat))
                inconsistent = False
                for r in range(n):
                    if all(mat[r][c] == 0 for c in range(n_vars)) and mat[r][-1] != 0:
                        inconsistent = True; break
                if inconsistent:
                    self.log.appendPlainText("Sistema inconsistente")
                    self._update_result_panel("INCONSISTENTE", pivot_cols, [i+1 for i in range(n_vars) if i not in pivot_cols], "DEPENDIENTE" if len(pivot_cols) < n_vars else "INDEPENDIENTE", None)
                else:
                    sol = [Fraction(0)] * n_vars
                    for i in range(n_vars-1, -1, -1):
                        s = mat[i][-1]
                        for j in range(i+1, n_vars):
                            s -= mat[i][j] * sol[j]
                        sol[i] = s / (mat[i][i] if mat[i][i] != 0 else Fraction(1))
                    self.log.appendPlainText("Solución por Gauss:")
                    for i, val in enumerate(sol, start=1):
                        self.log.appendPlainText(f"x{i} = {self._fmt_val(val)}")
                    self._update_result_panel("ÚNICA" if len(pivot_cols) == n_vars else "INFINITAS", pivot_cols, [i+1 for i in range(n_vars) if i not in pivot_cols], "INDEPENDIENTE" if len(pivot_cols) == n_vars else "DEPENDIENTE", sol)
            elif method == "Cramer":
                A = [row[:-1] for row in data]; b = [row[-1] for row in data]
                n = len(A)
                if any(len(row) != n for row in A):
                    self.log.appendPlainText("Cramer requiere matriz cuadrada")
                    self._update_result_panel("N/A", [], [], "DEPENDIENTE", None)
                    return
                detA, logA = operations_determinant.determinant_with_log(A)
                if detA == 0:
                    self.log.appendPlainText("Determinante de A es cero; Cramer no aplicable")
                    self._update_result_panel("INDETERMINADO", [], list(range(1, n+1)), "DEPENDIENTE", None)
                    return
                sol = []
                for i in range(n):
                    Ai = [row[:] for row in A]
                    for r in range(n):
                        Ai[r][i] = b[r]
                    detAi, _ = operations_determinant.determinant_with_log(Ai)
                    sol.append(detAi / detA)
                self.log.appendPlainText("Solución por Cramer:")
                for i, val in enumerate(sol, start=1):
                    self.log.appendPlainText(f"x{i} = {self._fmt_val(val)}")
                self._update_result_panel("ÚNICA", list(range(n)), [], "INDEPENDIENTE", sol)
            else:
                A = [row[:-1] for row in data]; b = [row[-1] for row in data]
                n = len(A)
                if n != 3 or any(len(row) != 3 for row in A):
                    self.log.appendPlainText("Sarrus solo disponible para 3×3")
                    self._update_result_panel("N/A", [], [], "DEPENDIENTE", None)
                    return
                detA, _ = operations_determinant.determinant_with_log(A)
                if detA == 0:
                    self.log.appendPlainText("Determinante de A es cero; Sarrus no aplicable")
                    self._update_result_panel("INDETERMINADO", [], [1,2,3], "DEPENDIENTE", None)
                    return
                sol = []
                for i in range(3):
                    Ai = [row[:] for row in A]
                    for r in range(3):
                        Ai[r][i] = b[r]
                    detAi, _ = operations_determinant.determinant_with_log(Ai)
                    sol.append(detAi / detA)
                self.log.appendPlainText("Solución por Sarrus/Cramer 3×3:")
                for i, val in enumerate(sol, start=1):
                    self.log.appendPlainText(f"x{i} = {self._fmt_val(val)}")
                self._update_result_panel("ÚNICA", [0,1,2], [], "INDEPENDIENTE", sol)
        except Exception as e:
            self.log.appendPlainText(f"Error: {e}")

    def clear(self):
        self.table.clear(); self.table.setRowCount(0); self.table.setColumnCount(0)
        self.log.clear()
        self._update_result_panel("", [], [], "", None)

    def open_equations_dialog(self):
        dlg = QDialog(self); dlg.setWindowTitle("Introducir ecuaciones")
        lay = QVBoxLayout(dlg)
        info = QLabel("Introduce ecuaciones separadas por comas. Ej: 2x1+3x2+3x3=0, 3x1+4x2-x3=1, x3=10")
        edit = QPlainTextEdit(); edit.setPlaceholderText("2x1+3x2+3x3=0, 3x1+4x2-x3=1, x3=10")
        lay.addWidget(info); lay.addWidget(edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        lay.addWidget(bb)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        if dlg.exec():
            text = edit.toPlainText().strip()
            try:
                A, b = self._parse_equations(text)
                rows = len(A); cols = len(A[0])
                self.spin_rows.setValue(rows); self.spin_cols.setValue(cols)
                self.table.setRowCount(rows); self.table.setColumnCount(cols + 1)
                for r in range(rows):
                    for c in range(cols):
                        self.table.setItem(r, c, QTableWidgetItem(str(float(A[r][c]))))
                    self.table.setItem(r, cols, QTableWidgetItem(str(float(b[r]))))
                self._set_headers(rows, cols)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _parse_equations(self, text: str):
        parts = [p.strip() for p in re.split(r"[\n,]+", text) if p.strip()]
        terms = []
        max_var = 0
        for eq in parts:
            if "=" not in eq:
                raise ValueError("Ecuación sin '='")
            left, right = eq.split("=", 1)
            left = left.replace(" ", "")
            pos = 0
            coef_map = {}
            while pos < len(left):
                sign = 1
                if left[pos] in "+-":
                    sign = -1 if left[pos] == '-' else 1
                    pos += 1
                num = ''
                while pos < len(left) and left[pos].isdigit():
                    num += left[pos]; pos += 1
                if pos >= len(left) or left[pos].lower() != 'x':
                    raise ValueError("Se esperaba variable xk")
                pos += 1
                var_idx = ''
                while pos < len(left) and left[pos].isdigit():
                    var_idx += left[pos]; pos += 1
                if not var_idx:
                    raise ValueError("Índice de variable faltante")
                k = int(var_idx)
                max_var = max(max_var, k)
                coef = Fraction(sign) * (parse_fraction(num) if num else Fraction(1))
                coef_map[k] = coef_map.get(k, Fraction(0)) + coef
            b = parse_fraction(right.strip())
            terms.append((coef_map, b))
        A = []
        B = []
        for coef_map, b in terms:
            row = [Fraction(0)] * max_var
            for k, v in coef_map.items():
                if 1 <= k <= max_var:
                    row[k-1] = v
            A.append(row); B.append(b)
        return A, B

    def _set_headers(self, rows: int, cols: int):
        self.table.setHorizontalHeaderLabels([*(f"x{i+1}" for i in range(cols)), "b"])
        self.table.setVerticalHeaderLabels([str(i+1) for i in range(rows)])

    def _fmt_val(self, x) -> str:
        try:
            val = float(x)
            s = f"{val:.6f}".rstrip('0').rstrip('.')
            return s if s else "0"
        except Exception:
            return str(x)

    def _format_matrix_lines(self, mat):
        rows = []
        for r in mat:
            left = "  " + "  ".join(f"{self._fmt_val(v):>8}" for v in r[:-1])
            right = self._fmt_val(r[-1])
            rows.append(f"[{left} | {right:>8}]")
        return "\n".join(rows)

    def _update_result_panel(self, status, pivot_cols, free_vars, indep, sol):
        self.res_status.setText(f"Estado: {status}" if status else "Estado: —")
        piv_txt = ", ".join(str(p+1) for p in pivot_cols) if pivot_cols else "—"
        self.res_pivots.setText(f"Columnas pivote: {piv_txt}")
        free_txt = ", ".join(f"x{v}" for v in free_vars) if free_vars else "—"
        self.res_free.setText(f"Variables libres: {free_txt}")
        self.res_indep.setText(f"Columnas de A: {indep}" if indep else "Columnas de A: —")
        n_vars = max(0, (self.table.columnCount() - 1))
        if sol:
            n_vars = max(n_vars, len(sol))
        self.res_vars.setRowCount(n_vars)
        for i in range(n_vars):
            self.res_vars.setItem(i, 0, QTableWidgetItem(f"x{i+1}"))
            val_text = "—"
            if sol and i < len(sol):
                val_text = self._fmt_val(sol[i])
            else:
                if status in ("INFINITAS", "INDETERMINADO") and (i+1) in free_vars:
                    val_text = "Libre"
                elif status == "INCONSISTENTE":
                    val_text = "No aplica"
            self.res_vars.setItem(i, 1, QTableWidgetItem(val_text))

class RootFindingPage(QWidget):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.current_method = "Bisección"
        self.last_root = None
        self.last_func = ""
        self.last_params = {}
        main = QVBoxLayout(self); main.setContentsMargins(24, 24, 24, 24); main.setSpacing(16)

        left = QVBoxLayout(); left.setSpacing(12); left.setAlignment(Qt.AlignTop)
        config_card = QFrame(); config_card.setObjectName("configCard")
        config_card.setStyleSheet(
            f"""
            QFrame#configCard {{
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
            }}
            """
        )
        config_card.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        config_card.setFixedWidth(520)
        card = QVBoxLayout(config_card); card.setContentsMargins(16,16,16,16); card.setSpacing(12)

        title = QLabel("Configuración")
        title.setStyleSheet(f"color:{self.colors['text']};")
        title.setFont(QtGui.QFont("Segoe UI", 18, QtGui.QFont.Bold))
        card.addWidget(title)

        lbl_prev = QLabel("Previsualización:"); lbl_prev.setStyleSheet(f"color:{self.colors['text']};")
        card.addWidget(lbl_prev)
        self.preview_fig = Figure(figsize=(3, 0.6), dpi=150)
        self.preview_ax = self.preview_fig.add_subplot(111); self.preview_ax.axis("off")
        self.preview_canvas = FigureCanvasQTAgg(self.preview_fig); self.preview_canvas.setFixedHeight(60)
        card.addWidget(self.preview_canvas)

        self.func = QLineEdit(); self.func.setPlaceholderText("tan(x) - x")
        card.addWidget(self.func)

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
            btn.setMinimumHeight(38)
            btn.setFont(QtGui.QFont("Segoe UI", 12))
            btn.setStyleSheet(
                f"background: rgba(255,255,255,0.06); color:{self.colors['text']}; border-radius:10px; padding:10px 14px; border:1px solid rgba(255,255,255,0.10);"
            )
            method_bar.addWidget(btn)
        card.addLayout(method_bar)

        grid = QGridLayout(); grid.setHorizontalSpacing(10); grid.setVerticalSpacing(6)
        for text in ("a / x₀:", "b / x₁:", "Tolerancia:", "Máx. iteraciones:"):
            lbl = QLabel(text); lbl.setStyleSheet(f"color:{self.colors['text']};"); grid.addWidget(lbl, *(divmod(list(("a / x₀:", "b / x₁:", "Tolerancia:", "Máx. iteraciones:")).index(text), 2)))
        self.a = QDoubleSpinBox(); self.a.setRange(-1e6, 1e6); self.a.setDecimals(8); self.a.setValue(-1.0)
        self.b = QDoubleSpinBox(); self.b.setRange(-1e6, 1e6); self.b.setDecimals(8); self.b.setValue(1.0)
        self.tol = QDoubleSpinBox(); self.tol.setRange(1e-12, 1.0); self.tol.setDecimals(10); self.tol.setValue(1e-4)
        self.max_iter = QSpinBox(); self.max_iter.setRange(1, 10000); self.max_iter.setValue(100)
        grid.addWidget(self.a, 0, 1); grid.addWidget(self.b, 0, 3); grid.addWidget(self.tol, 1, 1); grid.addWidget(self.max_iter, 1, 3)
        card.addLayout(grid)

        actions = QHBoxLayout()
        self.btn_calc = QPushButton("Calcular")
        self.btn_plot = QPushButton("Graficar")
        self.btn_suggest = QPushButton("Sugerir intervalo")
        self.btn_clear = QPushButton("Limpiar")
        for btn in (self.btn_calc, self.btn_plot, self.btn_suggest, self.btn_clear):
            btn.setCursor(Qt.PointingHandCursor)
            actions.addWidget(btn)
        card.addLayout(actions)

        keypad = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"), ("ln(x)", "ln(x)"), ("log(x)", "log(x)"), ("√", "sqrt("),
            ("x²", "x^2"), ("x³", "x^3"), ("1/x", "1/x"), ("x", "x"), ("π", "pi"), ("e", "e"),
            ("|x|", "abs(x)"), ("+", "+"), ("-", "-"), ("×", "*"), ("÷", "/"), ("^", "^"),
            ("Borrar", "<DEL>"), ("(", "("), (")", ")")
        ]
        grid_keys = QGridLayout(); grid_keys.setHorizontalSpacing(12); grid_keys.setVerticalSpacing(10)
        for idx, (text, value) in enumerate(keypad):
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(34)
            btn.setFont(QtGui.QFont("Segoe UI", 12))
            btn.setStyleSheet(
                f"background: rgba(255,255,255,0.06); color:{self.colors['text']}; border-radius:12px; padding:8px 12px; border:1px solid rgba(255,255,255,0.10);"
            )
            btn.clicked.connect(lambda _, v=value: self.insert_text(v))
            grid_keys.addWidget(btn, idx // 6, idx % 6)
        card.addLayout(grid_keys)

        left.addWidget(config_card)

        right = QVBoxLayout(); right.setSpacing(10)
        self.figure = Figure(figsize=(7.2, 5.0), dpi=150)
        self.plot_ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasQTAgg(self.figure); self.canvas.setMinimumHeight(420)
        self.toolbar = NavigationToolbar2QT(self.canvas)

        self.output_tabs = QTabWidget()
        tab_graph = QWidget(); lay_graph = QVBoxLayout(tab_graph); lay_graph.setContentsMargins(0,0,0,0); lay_graph.setSpacing(6)
        lay_graph.addWidget(self.toolbar); lay_graph.addWidget(self.canvas)
        self.output_tabs.addTab(tab_graph, "Gráfica")

        tab_results = QWidget(); lay_res = QVBoxLayout(tab_results); lay_res.setContentsMargins(0,0,0,0); lay_res.setSpacing(8)
        lbl_res = QLabel("Resultados"); lbl_res.setStyleSheet(f"color:{self.colors['text']};")
        lay_res.addWidget(lbl_res)
        controls_res = QHBoxLayout(); controls_res.addStretch(1)
        controls_res.addWidget(QLabel("Tamaño texto:", parent=self)); self.slider_font = QSlider(Qt.Horizontal)
        self.slider_font.setRange(8, 16); self.slider_font.setValue(10)
        controls_res.addWidget(self.slider_font); lay_res.addLayout(controls_res)
        self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(220); self.log.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log.setFont(QtGui.QFont("Consolas", 10)); lay_res.addWidget(self.log)
        self.output_tabs.addTab(tab_results, "Resultados")

        right.addWidget(self.output_tabs)

        left_widget = QWidget(); left_widget.setLayout(left)
        left_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_widget.setFixedWidth(520)
        layout_top = QHBoxLayout(); layout_top.setContentsMargins(0, 0, 0, 0)
        layout_top.addWidget(left_widget)
        layout_top.setAlignment(left_widget, Qt.AlignTop)
        layout_top.addLayout(right)
        layout_top.setStretch(0, 5)
        layout_top.setStretch(1, 7)
        main.addLayout(layout_top)
        main.setStretch(0, 3)

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
                btn.setStyleSheet(
                    f"background:{self.colors['accent']}; color:black; border-radius:10px; padding:10px 14px; font-weight:600; border:1px solid rgba(0,0,0,0.0);"
                )
            else:
                btn.setStyleSheet(
                    f"background: rgba(255,255,255,0.06); color:{self.colors['text']}; border-radius:10px; padding:10px 14px; border:1px solid rgba(255,255,255,0.10);"
                )
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
            self.preview_ax.text(0.02, 0.5, f"$f(x) = {latex}$", fontsize=12, va="center")
        self.preview_fig.tight_layout(); self.preview_canvas.draw_idle()

    def _to_mathtext(self, s: str) -> str:
        try:
            t = s
            import re
            # caso especial: 1/x - something -> \frac{1}{x - something}
            t = re.sub(r"^\s*1\s*/\s*x\s*-\s*(.+)$", r"\\frac{1}{x-\1}", t)
            # sqrt -> \sqrt{}
            t = re.sub(r"sqrt\s*\(\s*([^()]*)\s*\)", r"\\sqrt{\1}", t)
            # ln/log -> \ln{} / \log{}
            t = re.sub(r"\bln\s*\(\s*([^()]*)\s*\)", r"\\ln{\1}", t)
            t = re.sub(r"\blog\s*\(\s*([^()]*)\s*\)", r"\\log{\1}", t)
            # exponentes: a^(b)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*\(\s*([^()]*)\s*\)", r"\1^{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*(-?[A-Za-z0-9\.]+)", r"\1^{\2}", t)
            # fracciones comunes
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*([A-Za-z0-9\.]+)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"(?<![A-Za-z0-9_])([\-]?[A-Za-z0-9\.]+)\s*/\s*([\-]?[A-Za-z0-9\.]+)(?![A-Za-z0-9_])", r"\\frac{\1}{\2}", t)
            return self._normalize_exponents(t)
        except Exception:
            return self._normalize_exponents(s)

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
            elif ch == "^" and i + 1 >= n:
                i += 1
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
            self.preview_ax.text(0.02, 0.5, f"$f(x) = {latex}$", fontsize=12, va="center")
        self.preview_fig.tight_layout(); self.preview_canvas.draw_idle()

    def _to_mathtext(self, s: str) -> str:
        try:
            t = s
            import re
            t = re.sub(r"^\s*1\s*/\s*x\s*-\s*(.+)$", r"\\frac{1}{x-\1}", t)
            t = re.sub(r"sqrt\s*\(\s*([^()]*)\s*\)", r"\\sqrt{\1}", t)
            t = re.sub(r"\bln\s*\(\s*([^()]*)\s*\)", r"\\ln{\1}", t)
            t = re.sub(r"\blog\s*\(\s*([^()]*)\s*\)", r"\\log{\1}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*\(\s*([^()]*)\s*\)", r"\1^{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*(-?[A-Za-z0-9\.]+)", r"\1^{\2}", t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*([A-Za-z0-9\.]+)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"(?<![A-Za-z0-9_])([\-]?[A-Za-z0-9\.]+)\s*/\s*([\-]?[A-Za-z0-9\.]+)(?![A-Za-z0-9_])", r"\\frac{\1}{\2}", t)
            return self._normalize_exponents(t)
        except Exception:
            return self._normalize_exponents(s)

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
            if ch == "^":
                # incompleto al final: ignorar
                if i + 1 >= n:
                    i += 1
                    continue
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
                    continue
                # leer token con signo opcional
                start = i
                if expr[start] == "-":
                    start += 1
                end = start
                while end < n and (expr[end].isalnum() or expr[end] in "._πe"):
                    end += 1
                # si no hay token válido, omitir '^'
                if end == i or (expr[i] == '-' and end == i + 1):
                    out.append("")
                else:
                    out.append("^{")
                    out.append(expr[i:end])
                    out.append("}")
                i = end
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
            self.preview_ax.text(0.02, 0.5, f"$f(x) = {latex}$", fontsize=12, va="center")
        self.preview_fig.tight_layout(); self.preview_canvas.draw_idle()

    def _to_mathtext(self, s: str) -> str:
        try:
            t = s
            import re
            t = re.sub(r"^\s*1\s*/\s*x\s*-\s*(.+)$", r"\\frac{1}{x-\1}", t)
            t = re.sub(r"sqrt\s*\(\s*([^()]*)\s*\)", r"\\sqrt{\1}", t)
            t = re.sub(r"\bln\s*\(\s*([^()]*)\s*\)", r"\\ln{\1}", t)
            t = re.sub(r"\blog\s*\(\s*([^()]*)\s*\)", r"\\log{\1}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*\(\s*([^()]*)\s*\)", r"\1^{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*(-?[A-Za-z0-9\.]+)", r"\1^{\2}", t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*([A-Za-z0-9\.]+)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"(?<![A-Za-z0-9_])([\-]?[A-Za-z0-9\.]+)\s*/\s*([\-]?[A-Za-z0-9\.]+)(?![A-Za-z0-9_])", r"\\frac{\1}{\2}", t)
            return self._normalize_exponents(t)
        except Exception:
            return self._normalize_exponents(s)

    def _normalize_exponents(self, expr: str) -> str:
        out = []
        i = 0
        n = len(expr)
        while i < n:
            ch = expr[i]
            if ch == "^":
                # si es el último carácter, ignorar para evitar errores
                if i + 1 >= n:
                    i += 1
                    continue
                # si ya viene en formato LaTeX ^{...}, no tocar
                if expr[i + 1] == "{":
                    out.append("^")
                    i += 1
                    continue
                i += 1
                if expr[i] == "(":
                    # convertir ^(expr) -> ^{expr}
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
                    # token simple con signo opcional
                    start = i
                    if expr[start] == "-":
                        start += 1
                    end = start
                    while end < n and (expr[end].isalnum() or expr[end] in "._πe"):
                        end += 1
                    if end == i or (expr[i] == '-' and end == i + 1):
                        # sin token válido, omitir '^'
                        pass
                    else:
                        out.append("^{")
                        out.append(expr[i:end])
                        out.append("}")
                    i = end
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

        home = QWidget()
        home_layout = QVBoxLayout(home); home_layout.setContentsMargins(24,24,24,24); home_layout.setSpacing(18); home_layout.setAlignment(Qt.AlignTop)

        hero = QFrame(); hero.setObjectName("homeHero")
        hero.setStyleSheet(
            f"""
            QFrame#homeHero {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {self.colors['secondary_bg']}, stop:1 rgba(255,149,0,0.18));
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 16px;
            }}
            """
        )
        hero_layout = QVBoxLayout(hero); hero_layout.setContentsMargins(18,18,18,18); hero_layout.setSpacing(6); hero_layout.setAlignment(Qt.AlignTop)
        title = QLabel("Calculadora de Álgebra")
        title.setStyleSheet(f"color:{self.colors['accent']};")
        title.setFont(QtGui.QFont("Segoe UI", 28, QtGui.QFont.Bold))
        subtitle = QLabel("Selecciona una sección para comenzar")
        subtitle.setStyleSheet(f"color:{self.colors['text_secondary']};")
        hero_layout.addWidget(title, alignment=Qt.AlignLeft)
        hero_layout.addWidget(subtitle, alignment=Qt.AlignLeft)
        home_layout.addWidget(hero)

        options_card = QFrame(); options_card.setObjectName("homeOptions")
        options_card.setStyleSheet(
            f"""
            QFrame#homeOptions {{
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
            }}
            """
        )
        options_layout = QVBoxLayout(options_card); options_layout.setContentsMargins(18,18,18,18); options_layout.setSpacing(14); options_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        btn_matrices = QPushButton("🧮  Matrices"); btn_sis = QPushButton("∑  Sistema de ecuaciones lineales"); btn_root = QPushButton("√  Métodos numéricos")
        for b in (btn_matrices, btn_sis, btn_root):
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(48)
            b.setFixedWidth(420)
            b.setStyleSheet(
                f"""
                QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {self.colors['secondary_bg']}, stop:1 rgba(255,149,0,0.16)); color:{self.colors['text']}; border-radius:12px; padding:12px 16px; border:1px solid rgba(255,255,255,0.10); text-align:left; }}
                QPushButton:hover {{ background: rgba(255,255,255,0.10); }}
                QPushButton:pressed {{ background: rgba(255,255,255,0.14); }}
                """
            )
            options_layout.addWidget(b, alignment=Qt.AlignHCenter)
            info = QLabel(" ")
            info.setStyleSheet(f"color:{self.colors['text_secondary']};")
            options_layout.addWidget(info, alignment=Qt.AlignHCenter)
        home_layout.addWidget(options_card)

        try:
            from PySide6.QtWidgets import QGraphicsDropShadowEffect
            sh1 = QGraphicsDropShadowEffect(hero); sh1.setBlurRadius(20); sh1.setColor(QtGui.QColor(0,0,0,80)); sh1.setOffset(0,4); hero.setGraphicsEffect(sh1)
            sh2 = QGraphicsDropShadowEffect(options_card); sh2.setBlurRadius(20); sh2.setColor(QtGui.QColor(0,0,0,80)); sh2.setOffset(0,4); options_card.setGraphicsEffect(sh2)
        except Exception:
            pass

        tabs.addTab(home, "Inicio")
        tabs.addTab(MatricesPage(self.colors, self), "Matrices")
        tabs.addTab(GaussJordanPage(self.colors, self), "Sistema de ecuaciones lineales")
        tabs.addTab(RootFindingPage(self.colors, self), "Métodos numéricos")

        btn_matrices.clicked.connect(lambda: tabs.setCurrentIndex(1))
        btn_sis.clicked.connect(lambda: tabs.setCurrentIndex(2))
        btn_root.clicked.connect(lambda: tabs.setCurrentIndex(3))

        self.setCentralWidget(tabs)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
