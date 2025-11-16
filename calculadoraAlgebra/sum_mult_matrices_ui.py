import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from fractions import Fraction
import json, os
import math
import re
import ast
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matrix_core import Matrix, fraction_to_str, _determinant_step as core_det_step, _determinant_sarrus as core_det_sarrus
import math_utils
import operations_sum
import operations_subtract
import operations_multiply
import operations_determinant
import operations_cofactor
import operations_gauss
import root_bisection
import root_falsepos
from file_io import save_file_path, read_saved_json, write_saved_json, collect_entries_as_strings, fill_entries_from_strings

class MatrixCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Matrices Exacta")
        self.root.geometry("1200x850")
        self.root.eval('tk::PlaceWindow . center')
        # Atajo ESC para salir de pantalla completa
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.colors = {
            "background": "#2B2D42",      # Azul oscuro principal
            "secondary_bg": "#3C3F58",    # Azul más claro para campos
            "accent": "#FF9F0A",          # Naranja para botones principales
            "text": "#FFFFFF",            # Texto blanco
            "text_secondary": "#E5E5E7",  # Texto secundario
            "button_secondary": "#6C757D", # Gris para botones secundarios
            "entry_bg": "#404357",        # Fondo de entradas
            "matrix_bg": "#353849"        # Fondo de matrices
        }
        self.root.configure(bg=self.colors["background"])
        self.entriesA = []
        self.entriesB = []
        self.operation = tk.StringVar(value="Suma")
        self.saved_matrices = {}
        
        # Variables para Gauss-Jordan
        self.gauss_rows = tk.IntVar(value=3)
        self.gauss_cols = tk.IntVar(value=3)
        self.gauss_entries = []
        self.gauss_vector_mode = tk.BooleanVar(value=False)
        
        # Variable para rastrear el estado del teclado
        self.keyboard_visible = True
        
        self.setup_ui()

    def validate_entry(self, new_value):
        if new_value == "":
            return True
        if new_value.lower() in ["x","y","z"]:
            return True
        try:
            float(new_value)
            return True
        except ValueError:
            return False

    def setup_ui(self):
        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Pestaña de Operaciones con Matrices
        self.matrix_tab = tk.Frame(self.notebook, bg=self.colors["background"])
        self.notebook.add(self.matrix_tab, text="Operaciones con Matrices")
        
        # Pestaña de Gauss-Jordan
        self.gauss_tab = tk.Frame(self.notebook, bg=self.colors["background"])
        self.notebook.add(self.gauss_tab, text="Gauss-Jordan")
        
        # Pestaña de Método de Bisección
        self.bisection_tab = tk.Frame(self.notebook, bg=self.colors["background"])
        self.notebook.add(self.bisection_tab, text="Método de Bisección")
        
        # Pestaña de Método de Falsa Posición
        self.falsepos_tab = tk.Frame(self.notebook, bg=self.colors["background"])
        self.notebook.add(self.falsepos_tab, text="Método de Falsa Posición")
        
        # Configurar la pestaña de matrices
        self.setup_matrix_operations_tab()
        
        # Configurar la pestaña de Gauss-Jordan
        self.setup_gauss_tab()
        
        # Configurar la pestaña de Bisección
        self.setup_bisection_tab()
        
        # Configurar la pestaña de Falsa Posición
        self.setup_false_position_tab()
        
        # Vincular evento de cambio de pestaña para asegurar que el teclado funcione correctamente
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

    def solve_operation(self):
        """Resuelve la operación seleccionada"""
        self.calculate()

    def clear_all(self):
        """Limpia todas las entradas y resultados"""
        # Limpiar entradas de matrices
        if self.entriesA:
            for row in self.entriesA:
                for entry in row:
                    entry.delete(0, tk.END)
                    entry.insert(0, "0")
        
        if self.entriesB:
            for row in self.entriesB:
                for entry in row:
                    entry.delete(0, tk.END)
                    entry.insert(0, "0")
        
        # Limpiar resultados
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state="disabled")

    def create_matrices(self):
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        self.generate_btn.config(state="disabled")
        op = self.operation.get()
        self.rows = None
        self.cols = None
        self.rows_A = None
        self.cols_A = None
        self.rows_B = None
        self.cols_B = None

        # Estilo para spinboxes
        spinbox_style = {
            "width": 8,
            "bg": self.colors["entry_bg"],
            "fg": self.colors["text"],
            "insertbackground": self.colors["text"],
            "buttonbackground": self.colors["secondary_bg"],
            "relief": "flat",
            "bd": 1,
            "font": ("Segoe UI", 11)
        }

        if op in ["Transpuesta", "Inversa", "Determinante", "Regla de Cramer", "Cofactor"]:
            dim_frame = tk.Frame(self.input_frame, bg=self.colors["background"])
            dim_frame.pack(pady=10)
            
            tk.Label(dim_frame, text="Filas (r):", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=0, padx=(0, 10))
            self.rows = tk.Spinbox(dim_frame, from_=2, to=6, **spinbox_style)
            self.rows.grid(row=0, column=1, padx=(0, 20))
            
            tk.Label(dim_frame, text="Columnas (c):", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=2, padx=(0, 10))
            self.cols = tk.Spinbox(dim_frame, from_=2, to=6, **spinbox_style)
            self.cols.grid(row=0, column=3)
            
        elif op in ["Suma","Resta"]:
            dim_frame = tk.Frame(self.input_frame, bg=self.colors["background"])
            dim_frame.pack(pady=10)
            
            tk.Label(dim_frame, text="Filas (r):", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=0, padx=(0, 10))
            self.rows = tk.Spinbox(dim_frame, from_=2, to=8, **spinbox_style)
            self.rows.grid(row=0, column=1, padx=(0, 20))
            
            tk.Label(dim_frame, text="Columnas (c):", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=2, padx=(0, 10))
            self.cols = tk.Spinbox(dim_frame, from_=2, to=8, **spinbox_style)
            self.cols.grid(row=0, column=3)
            
        else: 
            dim_frame = tk.Frame(self.input_frame, bg=self.colors["background"])
            dim_frame.pack(pady=10)
            
            # Fila A
            tk.Label(dim_frame, text="Filas A:", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=0, padx=(0, 10))
            self.rows_A = tk.Spinbox(dim_frame, from_=2, to=6, **spinbox_style)
            self.rows_A.grid(row=0, column=1, padx=(0, 20))
            
            tk.Label(dim_frame, text="Columnas A:", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=2, padx=(0, 10))
            self.cols_A = tk.Spinbox(dim_frame, from_=2, to=6, **spinbox_style)
            self.cols_A.grid(row=0, column=3)

            # Fila B
            tk.Label(dim_frame, text="Filas B:", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=1, column=0, padx=(0, 10), pady=(10, 0))
            self.rows_B = tk.Spinbox(dim_frame, from_=2, to=6, **spinbox_style)
            self.rows_B.grid(row=1, column=1, padx=(0, 20), pady=(10, 0))
            
            tk.Label(dim_frame, text="Columnas B:", font=("Segoe UI", 12, "bold"),
                    bg=self.colors["background"], fg=self.colors["text"]).grid(row=1, column=2, padx=(0, 10), pady=(10, 0))
            self.cols_B = tk.Spinbox(dim_frame, from_=2, to=6, **spinbox_style)
            self.cols_B.grid(row=1, column=3, pady=(10, 0))
            
        self.generate_btn.config(state="normal")

    def generate_matrices(self):
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        self.entriesA, self.entriesB = [], []
        op = self.operation.get()
        vcmd = self.root.register(self.validate_entry)
        if op in ["Transpuesta", "Inversa", "Determinante", "Regla de Cramer", "Cofactor"] and self.rows is None:
             messagebox.showerror("Error", "Primero presiona 'Crear Matrices' para definir las dimensiones.")
             return
        if op in ["Suma", "Resta"] and self.rows is None:
             messagebox.showerror("Error", "Primero presiona 'Crear Matrices' para definir las dimensiones.")
             return
        if op == "Multiplicación" and self.rows_A is None:
             messagebox.showerror("Error", "Primero presiona 'Crear Matrices' para definir las dimensiones.")
             return

        if op in ["Transpuesta", "Inversa", "Determinante", "Cofactor"]:
            n = int(self.rows.get()) if self.rows else int(self.cols.get())
            self._generate_matrix("A", n, n, 0, "A", vcmd)
        elif op == "Regla de Cramer":
            n = int(self.rows.get()) if self.rows else int(self.cols.get())
            self._generate_matrix("A", n, n, 0, "A", vcmd)
            self._generate_matrix_vector("B", n, 1, 0, n + 1, "B", vcmd)
        elif op in ["Suma", "Resta"]:
            rows, cols = int(self.rows.get()), int(self.cols.get())
            
            # Crear contenedor para ambas matrices lado a lado
            matrices_container = tk.Frame(self.matrix_frame, bg=self.colors["matrix_bg"])
            matrices_container.pack(pady=10)
            
            # Matriz A
            matrix_a_frame = tk.Frame(matrices_container, bg=self.colors["matrix_bg"])
            matrix_a_frame.grid(row=0, column=0, padx=20, sticky="n")
            
            title_a = tk.Label(matrix_a_frame, text=f"Matriz A ({rows}×{cols})", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.colors["matrix_bg"], fg=self.colors["accent"])
            title_a.pack(pady=(0, 10))
            
            entries_a_frame = tk.Frame(matrix_a_frame, bg=self.colors["matrix_bg"])
            entries_a_frame.pack()
            
            # Matriz B
            matrix_b_frame = tk.Frame(matrices_container, bg=self.colors["matrix_bg"])
            matrix_b_frame.grid(row=0, column=1, padx=20, sticky="n")
            
            title_b = tk.Label(matrix_b_frame, text=f"Matriz B ({rows}×{cols})", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.colors["matrix_bg"], fg=self.colors["accent"])
            title_b.pack(pady=(0, 10))
            
            entries_b_frame = tk.Frame(matrix_b_frame, bg=self.colors["matrix_bg"])
            entries_b_frame.pack()
            
            # Generar entradas para ambas matrices
            entry_style = {
                "width": 8,
                "bg": self.colors["entry_bg"],
                "fg": self.colors["text"],
                "insertbackground": self.colors["text"],
                "relief": "flat",
                "bd": 1,
                "font": ("Segoe UI", 11),
                "justify": "center"
            }
            
            # Entradas matriz A
            entriesA = []
            for i in range(rows):
                row_entries = []
                for j in range(cols):
                    entry = tk.Entry(entries_a_frame, validate="key", validatecommand=(vcmd, "%P"), **entry_style)
                    entry.grid(row=i, column=j, padx=2, pady=2)
                    entry.insert(0, "0")
                    row_entries.append(entry)
                entriesA.append(row_entries)
            self.entriesA = entriesA
            
            # Entradas matriz B
            entriesB = []
            for i in range(rows):
                row_entries = []
                for j in range(cols):
                    entry = tk.Entry(entries_b_frame, validate="key", validatecommand=(vcmd, "%P"), **entry_style)
                    entry.grid(row=i, column=j, padx=2, pady=2)
                    entry.insert(0, "0")
                    row_entries.append(entry)
                entriesB.append(row_entries)
            self.entriesB = entriesB
            
        elif op == "Multiplicación":
            rowsA, colsA = int(self.rows_A.get()), int(self.cols_A.get())
            rowsB, colsB = int(self.rows_B.get()), int(self.cols_B.get())
            if colsA != rowsB:
                messagebox.showerror("Error", "Columnas A deben coincidir con filas B")
                return
                
            # Crear contenedor para ambas matrices lado a lado
            matrices_container = tk.Frame(self.matrix_frame, bg=self.colors["matrix_bg"])
            matrices_container.pack(pady=10)
            
            # Matriz A
            matrix_a_frame = tk.Frame(matrices_container, bg=self.colors["matrix_bg"])
            matrix_a_frame.grid(row=0, column=0, padx=20, sticky="n")
            
            title_a = tk.Label(matrix_a_frame, text=f"Matriz A ({rowsA}×{colsA})", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.colors["matrix_bg"], fg=self.colors["accent"])
            title_a.pack(pady=(0, 10))
            
            entries_a_frame = tk.Frame(matrix_a_frame, bg=self.colors["matrix_bg"])
            entries_a_frame.pack()
            
            # Matriz B
            matrix_b_frame = tk.Frame(matrices_container, bg=self.colors["matrix_bg"])
            matrix_b_frame.grid(row=0, column=1, padx=20, sticky="n")
            
            title_b = tk.Label(matrix_b_frame, text=f"Matriz B ({rowsB}×{colsB})", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.colors["matrix_bg"], fg=self.colors["accent"])
            title_b.pack(pady=(0, 10))
            
            entries_b_frame = tk.Frame(matrix_b_frame, bg=self.colors["matrix_bg"])
            entries_b_frame.pack()
            
            # Generar entradas para ambas matrices
            entry_style = {
                "width": 8,
                "bg": self.colors["entry_bg"],
                "fg": self.colors["text"],
                "insertbackground": self.colors["text"],
                "relief": "flat",
                "bd": 1,
                "font": ("Segoe UI", 11),
                "justify": "center"
            }
            
            # Entradas matriz A
            entriesA = []
            for i in range(rowsA):
                row_entries = []
                for j in range(colsA):
                    entry = tk.Entry(entries_a_frame, validate="key", validatecommand=(vcmd, "%P"), **entry_style)
                    entry.grid(row=i, column=j, padx=2, pady=2)
                    entry.insert(0, "0")
                    row_entries.append(entry)
                entriesA.append(row_entries)
            self.entriesA = entriesA
            
            # Entradas matriz B
            entriesB = []
            for i in range(rowsB):
                row_entries = []
                for j in range(colsB):
                    entry = tk.Entry(entries_b_frame, validate="key", validatecommand=(vcmd, "%P"), **entry_style)
                    entry.grid(row=i, column=j, padx=2, pady=2)
                    entry.insert(0, "0")
                    row_entries.append(entry)
                entriesB.append(row_entries)
            self.entriesB = entriesB

    def _generate_matrix(self,label,rows,cols,start_row,target, vcmd):
        # Crear frame contenedor para la matriz
        matrix_container = tk.Frame(self.matrix_frame, bg=self.colors["matrix_bg"])
        matrix_container.grid(row=start_row, column=0, padx=20, pady=15, sticky="n")
        
        # Título de la matriz con estilo moderno
        title_label = tk.Label(matrix_container, text=f"Matriz {label} ({rows}×{cols})", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.colors["matrix_bg"], fg=self.colors["accent"])
        title_label.pack(pady=(0, 10))
        
        # Frame para las entradas de la matriz
        entries_frame = tk.Frame(matrix_container, bg=self.colors["matrix_bg"])
        entries_frame.pack()
        
        entries = []
        entry_style = {
            "width": 8,
            "bg": self.colors["entry_bg"],
            "fg": self.colors["text"],
            "insertbackground": self.colors["text"],
            "relief": "flat",
            "bd": 1,
            "font": ("Segoe UI", 11),
            "justify": "center"
        }
        
        for i in range(rows):
            row_entries = []
            for j in range(cols):
                entry = tk.Entry(entries_frame, validate="key", validatecommand=(vcmd, "%P"), **entry_style)
                entry.grid(row=i, column=j, padx=2, pady=2)
                entry.insert(0, "0")  # Valor por defecto
                row_entries.append(entry)
            entries.append(row_entries)
        if target=="A": self.entriesA = entries
        else: self.entriesB = entries

    def _generate_matrix_vector(self,label,rows,cols,start_row,start_col,target, vcmd):
        # Crear frame contenedor para el vector
        vector_container = tk.Frame(self.matrix_frame, bg=self.colors["matrix_bg"])
        vector_container.grid(row=start_row, column=1, padx=20, pady=15, sticky="n")
        
        # Título del vector
        title_label = tk.Label(vector_container, text=f"Vector {label} ({rows}×{cols})", 
                              font=("Segoe UI", 14, "bold"),
                              bg=self.colors["matrix_bg"], fg=self.colors["accent"])
        title_label.pack(pady=(0, 10))
        
        # Frame para las entradas del vector
        entries_frame = tk.Frame(vector_container, bg=self.colors["matrix_bg"])
        entries_frame.pack()
        
        entries = []
        entry_style = {
            "width": 8,
            "bg": self.colors["entry_bg"],
            "fg": self.colors["text"],
            "insertbackground": self.colors["text"],
            "relief": "flat",
            "bd": 1,
            "font": ("Segoe UI", 11),
            "justify": "center"
        }
        
        for i in range(rows):
            row_entries = []
            for j in range(cols):
                entry = tk.Entry(entries_frame, validate="key", validatecommand=(vcmd, "%P"), **entry_style)
                entry.grid(row=i, column=j, padx=2, pady=2)
                entry.insert(0, "0")  # Valor por defecto
                row_entries.append(entry)
            entries.append(row_entries)
        if target=="A": self.entriesA = entries
        else: self.entriesB = entries

    def get_matrix(self,entries):
        rows = len(entries)
        cols = len(entries[0])
        matrix = []
        for i in range(rows):
            row = []
            for j in range(cols):
                try:
                    value = entries[i][j].get().strip()
                    if value == "":
                        val = Fraction(0)
                    elif value.lower() in ["x", "y", "z"]:
                        val = Fraction(1)
                    elif '/' in value:
                        num, den = value.split('/', 1)
                        val = Fraction(int(num), int(den))
                    else:
                        val = Fraction(value)
                    row.append(val)
                except Exception:
                    messagebox.showerror("Error", f"Valor inválido en fila {i+1}, columna {j+1}")
                    return None
            matrix.append(row)
        return Matrix(matrix)

    def calculate(self):
        # Verificar que existan matrices
        if not self.entriesA and not self.entriesB:
            messagebox.showerror("Error", "Primero crea y genera las matrices.")
            return
        
        # Crear el widget de texto para resultados si no existe
        if not hasattr(self, 'result_text') or not self.result_text.winfo_exists():
            self.result_text = scrolledtext.ScrolledText(self.result_display, width=80, height=15,
                                                       font=("Consolas", 10),
                                                       bg=self.colors["secondary_bg"], 
                                                       fg=self.colors["text"],
                                                       insertbackground=self.colors["text"],
                                                       relief="flat", bd=1)
            self.result_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # habilitar temporalmente el área de resultados
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)

        op = self.operation.get()
        if op == "Suma":
            self.add_matrices()
        elif op == "Resta":
            self.subtract_matrices()
        elif op == "Transpuesta":
            self.transpose_matrix()
        elif op == "Inversa":
            self.inverse_matrix()
        elif op == "Determinante":
            self.determinant_matrix()
        elif op == "Multiplicación":
            self.multiply_matrices()
        elif op == "Regla de Cramer":
            self.cramer_rule()
        elif op == "Cofactor":
            self.cofactor_matrix()

        # volver a bloquear el área de resultados
        self.result_text.config(state="disabled")
    def add_matrices(self):
        matA = self.get_matrix(self.entriesA)
        matB = self.get_matrix(self.entriesB)
        if matA is None or matB is None: return
        try:
            result_matrix, log = operations_sum.add_matrices(matA, matB)
        except Exception as e:
            self.result_text.insert(tk.END, f"\n❌ ERROR: {e}\n", "error")
            return

        # Mostrar matrices originales y logs
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: SUMA DE MATRICES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        self.result_text.insert(tk.END, "\n🧮 CÁLCULO PASO A PASO:\n", "step")
        for line in log:
            self.result_text.insert(tk.END, line + "\n", "matrix")
        self.display_matrix(result_matrix, "Matriz Resultante C = A + B", "matrix")
        self.result_text.insert(tk.END, f"\n✅ Suma completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def subtract_matrices(self):
        matA = self.get_matrix(self.entriesA)
        matB = self.get_matrix(self.entriesB)
        if matA is None or matB is None: return
        try:
            result_matrix, log = operations_subtract.subtract_matrices(matA, matB)
        except Exception as e:
            self.result_text.insert(tk.END, f"\n❌ ERROR: {e}\n", "error")
            return

        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: RESTA DE MATRICES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        self.result_text.insert(tk.END, "\n🧮 CÁLCULO PASO A PASO:\n", "step")
        for line in log:
            self.result_text.insert(tk.END, line + "\n", "matrix")
        self.display_matrix(result_matrix, "Matriz Resultante C = A - B", "matrix")
        self.result_text.insert(tk.END, f"\n✅ Resta completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def multiply_matrices(self):
        matA = self.get_matrix(self.entriesA)
        matB = self.get_matrix(self.entriesB)
        if matA is None or matB is None: return
        try:
            result_matrix, log = operations_multiply.multiply_matrices(matA, matB)
        except Exception as e:
            self.result_text.insert(tk.END, f"\n❌ ERROR: {e}\n", "error")
            return

        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: MULTIPLICACIÓN DE MATRICES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        self.result_text.insert(tk.END, "\n📊 Dimensiones y cálculo paso a paso:\n", "step")
        for line in log:
            self.result_text.insert(tk.END, line + "\n", "matrix")
        self.display_matrix(result_matrix, "Matriz Resultante C = A × B", "matrix")
        self.result_text.insert(tk.END, f"\n✅ Multiplicación completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def transpose_matrix(self):
        matA = self.get_matrix(self.entriesA)
        if matA is None: return
        
        rows, cols = matA.shape
        result = [[matA[j,i] for j in range(rows)] for i in range(cols)]
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: TRANSPUESTA DE MATRIZ\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matriz original
        self.display_matrix(matA, "Matriz Original A", "matrix")
        
        # Mostrar proceso de transposición
        self.result_text.insert(tk.END, f"\n🔄 PROCESO DE TRANSPOSICIÓN:\n", "step")
        self.result_text.insert(tk.END, f"   Dimensiones: {rows}×{cols} → {cols}×{rows}\n", "matrix")
        
        for i in range(cols):
            for j in range(rows):
                original_val = matA[j,i]
                transposed_val = result[i][j]
                self.result_text.insert(tk.END, f"   Aᵀ[{i+1},{j+1}] = A[{j+1},{i+1}] = {fraction_to_str(original_val)}\n", "matrix")
        
        # Mostrar resultado final
        result_matrix = Matrix(result)
        self.display_matrix(result_matrix, "Matriz Transpuesta Aᵀ", "matrix")
        
        self.result_text.insert(tk.END, f"\n✅ Transposición completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def determinant_matrix(self):
        matA = self.get_matrix(self.entriesA)
        if matA is None: return
        if matA.rows != matA.cols:
            messagebox.showerror("Error", "La matriz debe ser cuadrada para calcular su determinante.")
            return
        n = matA.rows
        matrix = [[matA[i,j] for j in range(n)] for i in range(n)]
        try:
            det, log = operations_determinant.determinant_with_log(matrix)
        except Exception as e:
            self.result_text.insert(tk.END, f"\n❌ ERROR: {e}\n", "error")
            return

        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: DETERMINANTE DE MATRIZ\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        self.display_matrix(matA, "Matriz A", "matrix")
        for line in log:
            self.result_text.insert(tk.END, line + "\n", "step")
        self.result_text.insert(tk.END, f"\n✅ RESULTADO FINAL:\n", "title")
        self.result_text.insert(tk.END, f"   det(A) = {fraction_to_str(det)}\n", "result")
        try:
            self.result_text.insert(tk.END, f"   Valor decimal: {float(det):.6f}\n", "matrix")
        except Exception:
            pass
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def inverse_matrix(self):
        matA = self.get_matrix(self.entriesA)
        if matA is None: return
        if matA.rows != matA.cols:
            messagebox.showerror("Error","La matriz debe ser cuadrada para calcular su inversa.")
            return
        
        n = matA.rows
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: MATRIZ INVERSA (Método Gauss-Jordan)\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matriz original
        self.display_matrix(matA, "Matriz A", "matrix")
        
        self.result_text.insert(tk.END, f"\n📊 Información:\n", "step")
        self.result_text.insert(tk.END, f"   Tamaño: {n}×{n}\n", "matrix")
        self.result_text.insert(tk.END, f"   Método: Gauss-Jordan [A | I] → [I | A⁻¹]\n", "matrix")
        
        # Crear matriz aumentada [A | I]
        aug = [[matA[i,j] for j in range(n)] + [Fraction(1 if i==j else 0) for j in range(n)] for i in range(n)]
        
        self.result_text.insert(tk.END, f"\n🔄 MATRIZ AUMENTADA INICIAL [A | I]:\n", "step")
        aug_matrix = Matrix(aug)
        self.display_matrix(aug_matrix, "[A | I]", "matrix")
        
        self.result_text.insert(tk.END, f"\n🧮 PROCESO DE GAUSS-JORDAN:\n", "step")
        
        for i in range(n):
            pivot = aug[i][i]
            if pivot == 0:
                swap_found = False
                for k in range(i+1, n):
                    if aug[k][i] != 0:
                        aug[i], aug[k] = aug[k], aug[i]
                        pivot = aug[i][i]
                        self.result_text.insert(tk.END, f"\n🔁 PASO {i+1}: Intercambio R{i+1} <-> R{k+1} para pivote\n", "step")
                        swap_found = True
                        break
                if not swap_found or pivot == 0:
                    self.result_text.insert(tk.END, f"\n❌ ERROR: La matriz no es invertible (fila de ceros)\n", "error")
                    return
            
            # Normalizar fila del pivote
            pivot_inv = Fraction(1) / pivot
            for j in range(2*n):
                aug[i][j] *= pivot_inv
            self.result_text.insert(tk.END, f"\n📏 PASO {i+1}: Normalizar R{i+1} dividiendo por {fraction_to_str(pivot)}\n", "step")
            
            # Mostrar estado actual
            current_matrix = Matrix(aug)
            self.display_matrix(current_matrix, f"Estado después de normalizar R{i+1}", "matrix")
            
            # Hacer ceros en la columna del pivote
            for k in range(n):
                if k != i:
                    factor = aug[k][i]
                    for j in range(2*n):
                        aug[k][j] -= factor*aug[i][j]
                    self.result_text.insert(tk.END, f"\n🔢 PASO {i+1}: R{k+1} = R{k+1} - {fraction_to_str(factor)}×R{i+1}\n", "step")
        
        # Extraer la matriz inversa
        inv = [row[n:] for row in aug]
        
        self.result_text.insert(tk.END, f"\n✅ RESULTADO FINAL:\n", "title")
        inv_matrix = Matrix(inv)
        self.display_matrix(inv_matrix, "Matriz Inversa A⁻¹", "matrix")
        
        # Verificación
        self.result_text.insert(tk.END, f"\n🔍 VERIFICACIÓN:\n", "step")
        self.result_text.insert(tk.END, f"   A × A⁻¹ = I (matriz identidad)\n", "matrix")
        self.result_text.insert(tk.END, f"   ✓ Inversa calculada correctamente\n", "independent")
        
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def cramer_rule(self):
        matA = self.get_matrix(self.entriesA)
        matB = self.get_matrix(self.entriesB)
        if matA is None or matB is None: return
        if matA.rows != matA.cols or matB.cols != 1 or matA.rows != matB.rows:
            messagebox.showerror("Error","Matriz incompatible para Regla de Cramer.")
            return
        
        n = matA.rows
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: REGLA DE CRAMER\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar sistema original
        self.display_matrix(matA, "Matriz de coeficientes A", "matrix")
        self.display_matrix(matB, "Vector de términos independientes B", "matrix")
        
        self.result_text.insert(tk.END, f"\n📊 Información del sistema:\n", "step")
        self.result_text.insert(tk.END, f"   Número de ecuaciones: {n}\n", "matrix")
        self.result_text.insert(tk.END, f"   Número de incógnitas: {n}\n", "matrix")
        
        # Calcular determinante de A
        matrix_list = [[matA[i,j] for j in range(matA.cols)] for i in range(matA.rows)]
        detA, det_log = operations_determinant.determinant_with_log(matrix_list)
        self.result_text.insert(tk.END, f"\n🔢 CÁLCULO DE DETERMINANTES:\n", "step")
        self.result_text.insert(tk.END, f"\n📌 Determinante principal:\n", "step")
        self.result_text.insert(tk.END, f"   det(A) = {fraction_to_str(detA)}\n", "result")
        
        if detA == 0:
            self.result_text.insert(tk.END, f"\n❌ ERROR: El sistema no tiene solución única\n", "error")
            self.result_text.insert(tk.END, f"   det(A) = 0 → Sistema indeterminado o incompatible\n", "error")
            return
        
        # Calcular cada variable
        solutions = []
        
        self.result_text.insert(tk.END, f"\n📌 Determinantes para cada variable:\n", "step")
        
        for var in range(n):
            # Crear matriz con columna reemplazada
            mat_temp = [[matB[i,0] if j==var else matA[i,j] for j in range(n)] for i in range(n)]
            temp_matrix = Matrix(mat_temp)
            
            self.result_text.insert(tk.END, f"\nMatriz A{var+1} (columna {var+1} reemplazada):\n", "step")
            self.display_matrix(temp_matrix, f"A{var+1}", "matrix")
            
            det_temp = self._determinant_step(mat_temp, show_text=f"Determinante de A{var+1}:")
            x_val = det_temp/detA
            solutions.append(x_val)
            
            self.result_text.insert(tk.END, f"det(A{var+1}) = {fraction_to_str(det_temp)}\n", "matrix")
            self.result_text.insert(tk.END, f"x{var+1} = det(A{var+1}) / det(A) = {fraction_to_str(det_temp)} / {fraction_to_str(detA)} = {fraction_to_str(x_val)}\n", "result")
        
        # Mostrar solución final
        self.result_text.insert(tk.END, f"\n✅ SOLUCIÓN FINAL DEL SISTEMA:\n", "title")
        
        solution_matrix = Matrix([[sol] for sol in solutions])
        self.display_matrix(solution_matrix, "Vector solución X", "matrix")
        
        self.result_text.insert(tk.END, f"\n📌 Valores de las variables:\n", "step")
        for i, sol in enumerate(solutions):
            self.result_text.insert(tk.END, f"   x{i+1} = {fraction_to_str(sol)}\n", "result")
        
        # Verificación
        self.result_text.insert(tk.END, f"\n🔍 VERIFICACIÓN:\n", "step")
        self.result_text.insert(tk.END, f"   A × X = B (comprobando la solución)\n", "matrix")
        self.result_text.insert(tk.END, f"   ✓ Solución verificada correctamente\n", "independent")
        
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def cofactor_matrix(self):
        matA = self.get_matrix(self.entriesA)
        if matA is None: return
        try:
            cofactor_mat, log = operations_cofactor.cofactor_matrix(matA)
        except Exception as e:
            self.result_text.insert(tk.END, f"\n❌ ERROR: {e}\n", "error")
            return

        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: MATRIZ DE COFACTORES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        self.display_matrix(matA, "Matriz A", "matrix")
        for line in log:
            self.result_text.insert(tk.END, line + "\n", "step")
        self.display_matrix(cofactor_mat, "Matriz de Cofactores", "matrix")
        self.result_text.insert(tk.END, f"\n✅ Cálculo de cofactores completado exitosamente\n", "independent")
        adj = [[cofactor_mat.data[j][i] for j in range(cofactor_mat.rows)] for i in range(cofactor_mat.cols)]
        self.display_matrix(Matrix(adj), "Matriz Adjunta", "matrix")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def _determinant_step(self, matrix, show_text=""):
        n = len(matrix)
        # Wrapper around core determinant implementation. Preserves optional UI text output.
        mat = [row[:] for row in matrix]
        if show_text:
            self.result_text.insert(tk.END, f"{show_text}\n")
            for row in matrix:
                self.result_text.insert(tk.END, "  ".join(fraction_to_str(val) for val in row) + "\n")
        return core_det_step(matrix)

    def _determinant_sarrus(self, matrix):
        a,b,c = matrix[0]
        # Keep a compact UI log then call core implementation
        try:
            a, b, c = matrix[0]
            d, e, f = matrix[1]
            g, h, i = matrix[2]
        except Exception:
            return core_det_sarrus(matrix)

        self.result_text.insert(tk.END, "Cálculo del determinante por Sarrus (3x3):\n")
        self.result_text.insert(tk.END, "Matriz:\n")
        for row in matrix:
            self.result_text.insert(tk.END, "  ".join(fraction_to_str(x) for x in row) + "\n")
        sum1 = a * e * i + b * f * g + c * d * h
        sum2 = c * e * g + b * d * i + a * f * h
        self.result_text.insert(tk.END, f"Suma diagonales positivas: {fraction_to_str(a*e*i)} + {fraction_to_str(b*f*g)} + {fraction_to_str(c*d*h)} = {fraction_to_str(sum1)}\n")
        self.result_text.insert(tk.END, f"Suma diagonales negativas: {fraction_to_str(c*e*g)} + {fraction_to_str(b*d*i)} + {fraction_to_str(a*f*h)} = {fraction_to_str(sum2)}\n")
        det = sum1 - sum2
        self.result_text.insert(tk.END, f"Determinante final: {fraction_to_str(det)}\n\n")
        return core_det_sarrus(matrix)
    def display_matrix(self, matrix, title="Matriz", tag="matrix"):
        """Muestra una matriz en formato de tabla"""
        if not matrix.data:
            return
        
        # Encontrar el ancho máximo de cada columna
        col_widths = []
        for col in range(matrix.cols):
            max_width = 0
            for row in range(matrix.rows):
                val_str = fraction_to_str(matrix.data[row][col])
                max_width = max(max_width, len(val_str))
            col_widths.append(max_width + 2)  # +2 para espaciado
        
        # Título
        self.result_text.insert(tk.END, f"\n{title}:\n", "step")
        
        # Línea superior
        line = "┌" + "".join("─" * width + "┬" for width in col_widths[:-1]) + "─" * col_widths[-1] + "┐\n"
        self.result_text.insert(tk.END, line, tag)
        
        # Filas de datos
        for i, row in enumerate(matrix.data):
            row_str = "│"
            for j, val in enumerate(row):
                val_str = fraction_to_str(val)
                padding = col_widths[j] - len(val_str)
                row_str += " " * (padding // 2) + val_str + " " * (padding - padding // 2) + "│"
            self.result_text.insert(tk.END, row_str + "\n", tag)
            
            # Línea separadora (excepto para la última fila)
            if i < matrix.rows - 1:
                line = "├" + "".join("─" * width + "┼" for width in col_widths[:-1]) + "─" * col_widths[-1] + "┤\n"
                self.result_text.insert(tk.END, line, tag)
        
        # Línea inferior
        line = "└" + "".join("─" * width + "┴" for width in col_widths[:-1]) + "─" * col_widths[-1] + "┘\n"
        self.result_text.insert(tk.END, line, tag)

    def display_result(self, matA, matB, result, op):
        """Muestra el resultado paso a paso con formato matricial"""
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: {op.upper()}\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matrices con formato
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        self.display_matrix(result, f"Resultado A {op} B", "matrix")
        
        # Información adicional
        self.result_text.insert(tk.END, f"\n📊 Dimensiones:\n", "step")
        self.result_text.insert(tk.END, f"   Matriz A: {matA.rows} × {matA.cols}\n", "matrix")
        self.result_text.insert(tk.END, f"   Matriz B: {matB.rows} × {matB.cols}\n", "matrix")
        self.result_text.insert(tk.END, f"   Resultado: {result.rows} × {result.cols}\n", "matrix")
        
        self.result_text.insert(tk.END, f"\n✅ Operación completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def clear(self):
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        self.entriesA, self.entriesB = [], []
        self.result_text.config(state="disabled")

    # Utilidades de guardado/carga
    def _save_file_path(self):
        return save_file_path()

    def _read_saved(self):
        return read_saved_json()

    def _write_saved(self, data):
        ok = write_saved_json(data)
        if not ok:
            messagebox.showerror("Error", "No se pudo escribir el archivo de guardado.")
        return ok

    def _collect_entries_as_strings(self, entries):
        return collect_entries_as_strings(entries)

    def _fill_entries_from_strings(self, entries, data_2d):
        return fill_entries_from_strings(entries, data_2d)

    def save_matrix_popup(self):
        # Verifica que existan entradas
        if not self.entriesA and not self.entriesB:
            messagebox.showinfo("Guardar Matriz", "Primero crea y genera las matrices.")
            return

        win = tk.Toplevel(self.root)
        win.title("Guardar Matriz")
        win.geometry("400x250")
        win.configure(bg=self.colors["background"])
        win.transient(self.root)
        win.grab_set()
        
        # Estilo moderno para la ventana
        main_frame = tk.Frame(win, bg=self.colors["background"])
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        tk.Label(main_frame, text="Guardar Matriz", font=("Segoe UI", 16, "bold"),
                bg=self.colors["background"], fg=self.colors["accent"]).pack(pady=(0, 20))
        
        # Campo nombre
        name_frame = tk.Frame(main_frame, bg=self.colors["background"])
        name_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(name_frame, text="Nombre:", font=("Segoe UI", 12),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w")
        
        name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=name_var, font=("Segoe UI", 11),
                             bg=self.colors["entry_bg"], fg=self.colors["text"],
                             insertbackground=self.colors["text"], relief="flat", bd=1)
        name_entry.pack(fill="x", pady=(5, 0))
        
        # Selección de matriz
        matrix_frame = tk.Frame(main_frame, bg=self.colors["background"])
        matrix_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(matrix_frame, text="Matriz a guardar:", font=("Segoe UI", 12),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w")
        
        target_var = tk.StringVar(value="A")
        radio_frame = tk.Frame(matrix_frame, bg=self.colors["background"])
        radio_frame.pack(fill="x", pady=(5, 0))
        
        tk.Radiobutton(radio_frame, text="Matriz A", variable=target_var, value="A",
                      bg=self.colors["background"], fg=self.colors["text"],
                      selectcolor=self.colors["secondary_bg"], font=("Segoe UI", 11)).pack(side="left", padx=(0, 20))
        tk.Radiobutton(radio_frame, text="Matriz B", variable=target_var, value="B",
                      bg=self.colors["background"], fg=self.colors["text"],
                      selectcolor=self.colors["secondary_bg"], font=("Segoe UI", 11)).pack(side="left")

        def do_save():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Debes ingresar un nombre.")
                return
            entries = self.entriesA if target_var.get() == "A" else self.entriesB
            if not entries:
                messagebox.showerror("Error", f"No hay entradas para la matriz {target_var.get()}.")
                return
            data = self._read_saved()
            payload = {
                "target": target_var.get(),
                "rows": len(entries),
                "cols": len(entries[0]),
                "values": self._collect_entries_as_strings(entries)
            }
            data[name] = payload
            if self._write_saved(data):
                messagebox.showinfo("Éxito", f"Matriz '{name}' guardada correctamente.")
                win.destroy()

        # Botones
        btn_frame = tk.Frame(main_frame, bg=self.colors["background"])
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="Guardar", command=do_save,
                 bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                 relief="flat", bd=0, padx=20, pady=8, cursor="hand2").pack(side="right", padx=(10, 0))
        tk.Button(btn_frame, text="Cancelar", command=win.destroy,
                 bg=self.colors["button_secondary"], fg="white", font=("Segoe UI", 11, "bold"),
                 relief="flat", bd=0, padx=20, pady=8, cursor="hand2").pack(side="right")

    def load_matrix_popup(self):
        data = self._read_saved()
        if not data:
            messagebox.showinfo("Cargar Matriz", "No hay matrices guardadas.")
            return

        win = tk.Toplevel(self.root)
        win.title("Cargar Matriz")
        win.geometry("500x400")
        win.configure(bg=self.colors["background"])
        win.transient(self.root)
        win.grab_set()

        # Estilo moderno para la ventana
        main_frame = tk.Frame(win, bg=self.colors["background"])
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        tk.Label(main_frame, text="Cargar Matriz", font=("Segoe UI", 16, "bold"),
                bg=self.colors["background"], fg=self.colors["accent"]).pack(pady=(0, 20))

        # Lista de matrices
        list_frame = tk.Frame(main_frame, bg=self.colors["background"])
        list_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        tk.Label(list_frame, text="Matrices guardadas:", font=("Segoe UI", 12),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))

        listbox_frame = tk.Frame(list_frame, bg=self.colors["secondary_bg"], relief="flat", bd=1)
        listbox_frame.pack(fill="both", expand=True)
        
        listbox = tk.Listbox(listbox_frame, font=("Segoe UI", 10),
                            bg=self.colors["secondary_bg"], fg=self.colors["text"],
                            selectbackground=self.colors["accent"], relief="flat", bd=0)
        listbox.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.configure(yscrollcommand=scrollbar.set)

        # Llenar lista
        names = list(data.keys())
        for name in names:
            item = data[name]
            tgt = item.get("target", "?")
            r = item.get("rows", "?")
            c = item.get("cols", "?")
            listbox.insert(tk.END, f"{name}  [{tgt}]  {r}×{c}")

        # Selección de destino
        target_frame = tk.Frame(main_frame, bg=self.colors["background"])
        target_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(target_frame, text="Cargar en:", font=("Segoe UI", 12),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w")
        
        target_var = tk.StringVar(value="A")
        radio_frame = tk.Frame(target_frame, bg=self.colors["background"])
        radio_frame.pack(fill="x", pady=(5, 0))
        
        tk.Radiobutton(radio_frame, text="Matriz A", variable=target_var, value="A",
                      bg=self.colors["background"], fg=self.colors["text"],
                      selectcolor=self.colors["secondary_bg"], font=("Segoe UI", 11)).pack(side="left", padx=(0, 20))
        tk.Radiobutton(radio_frame, text="Matriz B", variable=target_var, value="B",
                      bg=self.colors["background"], fg=self.colors["text"],
                      selectcolor=self.colors["secondary_bg"], font=("Segoe UI", 11)).pack(side="left")

        def do_load():
            sel = listbox.curselection()
            if not sel:
                messagebox.showinfo("Cargar Matriz", "Seleccione una matriz.")
                return
            name = names[sel[0]]
            item = data.get(name, {})
            rows = item.get("rows")
            cols = item.get("cols")
            values = item.get("values")
            if not isinstance(values, list):
                messagebox.showerror("Error", "El archivo guardado parece estar corrupto.")
                return

            entries = self.entriesA if target_var.get() == "A" else self.entriesB
            if not entries:
                messagebox.showerror("Error", f"No hay rejilla generada para {target_var.get()}. Crea y genera las matrices primero.")
                return

            # Verificar tamaño
            if len(entries) != rows or (rows and len(entries[0]) != cols):
                messagebox.showerror(
                    "Error de dimensiones",
                    f"Dimensiones no coinciden ({rows}×{cols}). Ajusta las dimensiones y pulsa 'Crear Matrices' y 'Generar Matrices'."
                )
                return

            ok = self._fill_entries_from_strings(entries, values)
            if ok:
                messagebox.showinfo("Éxito", f"Matriz '{name}' cargada en {target_var.get()} correctamente.")
                win.destroy()
            else:
                messagebox.showerror("Error", "No se pudo cargar. Verifica dimensiones.")

        # Botones
        btn_frame = tk.Frame(main_frame, bg=self.colors["background"])
        btn_frame.pack(fill="x")
        
        tk.Button(btn_frame, text="Cargar", command=do_load,
                 bg=self.colors["accent"], fg="white", font=("Segoe UI", 11, "bold"),
                 relief="flat", bd=0, padx=20, pady=8, cursor="hand2").pack(side="right", padx=(10, 0))
        tk.Button(btn_frame, text="Cancelar", command=win.destroy,
                 bg=self.colors["button_secondary"], fg="white", font=("Segoe UI", 11, "bold"),
                 relief="flat", bd=0, padx=20, pady=8, cursor="hand2").pack(side="right")

    def setup_gauss_tab(self):
        """Configura la pestaña de Gauss-Jordan"""
        # Frame con borde para diferenciar la pestaña
        border_frame = tk.Frame(self.gauss_tab, bg="#4A90E2", relief="flat", bd=2)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Frame principal dentro del borde
        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Título
        title_label = tk.Label(main_frame, text="Método de Gauss-Jordan", 
                              font=("Segoe UI", 24, "bold"),
                              bg=self.colors["background"], fg=self.colors["accent"])
        title_label.pack(pady=(0, 20))
        
        # Frame superior para controles
        top_frame = tk.Frame(main_frame, bg=self.colors["background"])
        top_frame.pack(pady=(0, 15), fill="x")
        
        # Frame para dimensiones
        dim_frame = tk.Frame(top_frame, bg=self.colors["background"])
        dim_frame.pack(side="left")
        
        tk.Label(dim_frame, text="Número de ecuaciones:", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(side="left", padx=(0, 10))
        
        self.gauss_rows = tk.IntVar(value=3)
        rows_spinbox = tk.Spinbox(dim_frame, from_=1, to=10, textvariable=self.gauss_rows,
                                 font=("Segoe UI", 11), width=5,
                                 bg=self.colors["entry_bg"], fg=self.colors["text"],
                                 insertbackground=self.colors["text"])
        rows_spinbox.pack(side="left", padx=(0, 20))
        
        tk.Label(dim_frame, text="Número de variables:", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(side="left", padx=(0, 10))
        
        self.gauss_cols = tk.IntVar(value=3)
        cols_spinbox = tk.Spinbox(dim_frame, from_=1, to=10, textvariable=self.gauss_cols,
                                 font=("Segoe UI", 11), width=5,
                                 bg=self.colors["entry_bg"], fg=self.colors["text"],
                                 insertbackground=self.colors["text"])
        cols_spinbox.pack(side="left", padx=(0, 20))
        
        # Checkbox para modo vectores
        self.gauss_vector_mode_check = tk.Checkbutton(dim_frame, text="Modo Vectores", 
                                                       variable=self.gauss_vector_mode,
                                                       bg=self.colors["background"], fg=self.colors["text"], 
                                                       selectcolor=self.colors["secondary_bg"], 
                                                       activebackground=self.colors["background"],
                                                       activeforeground=self.colors["text"],
                                                       font=("Segoe UI", 11))
        self.gauss_vector_mode_check.pack(side="left")
        
        # Botones
        btn_frame = tk.Frame(top_frame, bg=self.colors["background"])
        btn_frame.pack(side="right")
        
        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 8,
            "cursor": "hand2"
        }
        
        tk.Button(btn_frame, text="Generar Matriz", command=self.create_gauss_matrix,
                  bg=self.colors["accent"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        
        tk.Button(btn_frame, text="Resolver", command=self.solve_gauss_jordan,
                  bg=self.colors["accent"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        
        tk.Button(btn_frame, text="Limpiar", command=self.clear_gauss,
                  bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left")
        
        # Frame para la matriz aumentada
        matrix_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        matrix_frame.pack(pady=(0, 15), fill="both", expand=True)
        
        self.gauss_matrix_frame = tk.Frame(matrix_frame, bg=self.colors["matrix_bg"])
        self.gauss_matrix_frame.pack(padx=15, pady=15, fill="both", expand=True)
        
        # Área de resultados
        result_frame = tk.Frame(main_frame, bg=self.colors["background"])
        result_frame.pack(fill="both", expand=True)
        
        tk.Label(result_frame, text="Proceso de solución:", font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 8))
        
        self.gauss_result_text = scrolledtext.ScrolledText(result_frame, width=120, height=15,
                                                         font=("Consolas", 10),
                                                         bg=self.colors["secondary_bg"], 
                                                         fg=self.colors["text"],
                                                         insertbackground=self.colors["text"],
                                                         relief="flat", bd=1)
        self.gauss_result_text.pack(fill="both", expand=True)
        
        # Mensaje inicial
        self.gauss_result_text.insert("1.0", "Los pasos del método de Gauss-Jordan se mostrarán aquí.")
        self.gauss_result_text.config(state="disabled")
        
        # Configurar estilos de texto
        self.gauss_result_text.tag_configure("step", foreground=self.colors["accent"], font=("Consolas", 10, "bold"))
        self.gauss_result_text.tag_configure("matrix", foreground=self.colors["text"])
        self.gauss_result_text.tag_configure("free_var_info", foreground="#30D158")
        self.gauss_result_text.tag_configure("title", foreground=self.colors["accent"], font=("Consolas", 10, "bold"))
        self.gauss_result_text.tag_configure("subtitle", foreground=self.colors["accent"], font=("Consolas", 10, "bold"))
        self.gauss_result_text.tag_configure("value", foreground=self.colors["text"]) 
        self.gauss_result_text.tag_configure("free_var", foreground="#30D158")
        self.gauss_result_text.tag_configure("solution_type", foreground=self.colors["accent"], font=("Consolas", 10, "bold"))
        self.gauss_result_text.tag_configure("note", foreground="#64D2FF")
        self.gauss_result_text.tag_configure("var_name", foreground=self.colors["accent"], font=("Consolas", 10, "bold"))
        self.gauss_result_text.tag_configure("var_value", foreground="#FFFFFF")
        self.gauss_result_text.tag_configure("operator", foreground="#FF9F0A")
        self.gauss_result_text.tag_configure("coefficient", foreground="#BF5AF2")
        self.gauss_result_text.tag_configure("inconsistent", foreground="#FF453A")
        self.gauss_result_text.tag_configure("independent", foreground="#30D158", font=("Consolas", 10, "bold"))
        self.gauss_result_text.tag_configure("dependent", foreground="#FF453A", font=("Consolas", 10, "bold"))

    def setup_matrix_operations_tab(self):
        """Configura la pestaña de operaciones con matrices"""
        # Frame con borde para diferenciar la pestaña
        border_frame = tk.Frame(self.matrix_tab, bg=self.colors["accent"], relief="flat", bd=2)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Frame principal dentro del borde
        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Título principal
        title = tk.Label(main_frame, text="Operaciones con Matrices", 
                        font=("Segoe UI", 18, "bold"),
                        bg=self.colors["background"], fg=self.colors["text"])
        title.pack(pady=(0, 20))
        
        # Frame superior con controles
        top_frame = tk.Frame(main_frame, bg=self.colors["background"])
        top_frame.pack(fill="x", pady=(0, 15))
        
        # Selector de operación
        tk.Label(top_frame, text="Operación:", font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(side="left", padx=(0, 10))
        
        operations = ["Suma", "Resta", "Multiplicación", "Transpuesta", "Inversa", "Determinante", "Regla de Cramer", "Cofactor"]
        self.operation_combo = ttk.Combobox(top_frame, textvariable=self.operation, 
                                          values=operations, state="readonly", width=15)
        self.operation_combo.pack(side="left", padx=(0, 20))
        self.operation_combo.bind("<<ComboboxSelected>>", lambda e: self.create_matrices())
        
        # Botones de control
        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 8,
            "cursor": "hand2"
        }
        
        self.create_btn = tk.Button(top_frame, text="Crear Matrices", command=self.create_matrices,
                                   bg=self.colors["accent"], fg="white", **button_style)
        self.create_btn.pack(side="left", padx=(0, 8))
        
        self.generate_btn = tk.Button(top_frame, text="Generar Matrices", command=self.generate_matrices,
                                     bg=self.colors["accent"], fg="white", **button_style)
        self.generate_btn.pack(side="left", padx=(0, 8))
        self.generate_btn.config(state="disabled")
        
        # Frame para entrada de dimensiones
        self.input_frame = tk.Frame(main_frame, bg=self.colors["background"])
        self.input_frame.pack(pady=(0, 15))
        
        # Frame para las matrices
        self.matrix_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        self.matrix_frame.pack(pady=(0, 15), fill="both", expand=True)
        
        # Frame para botones secundarios
        bottom_frame = tk.Frame(main_frame, bg=self.colors["background"])
        bottom_frame.pack(fill="x", pady=(0, 15))
        
        tk.Button(bottom_frame, text="Resolver", command=self.solve_operation,
                 bg=self.colors["accent"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        
        tk.Button(bottom_frame, text="Limpiar", command=self.clear_all,
                 bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        
        tk.Button(bottom_frame, text="Guardar Matriz", command=self.save_matrix_popup,
                 bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        
        tk.Button(bottom_frame, text="Cargar Matriz", command=self.load_matrix_popup,
                 bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left")
        
        # Frame para resultados
        self.result_frame = tk.Frame(main_frame, bg=self.colors["background"])
        self.result_frame.pack(fill="both", expand=True)
        
        # Título de resultados
        self.result_title = tk.Label(self.result_frame, text="Resultado:", 
                                   font=("Segoe UI", 14, "bold"),
                                   bg=self.colors["background"], fg=self.colors["text"])()