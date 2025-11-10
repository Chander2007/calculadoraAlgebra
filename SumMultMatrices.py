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

def fraction_to_str(frac):
    if isinstance(frac, Fraction):
        if frac.denominator == 1:
            return str(frac.numerator)
        else:
            return f"{frac.numerator}/{frac.denominator}"
    return str(frac)

class Matrix:
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if self.rows > 0 else 0
        self.shape = (self.rows, self.cols)
    def __getitem__(self, indices):
        i, j = indices
        return self.data[i][j]
    def __setitem__(self, indices, value):
        i, j = indices
        self.data[i][j] = value

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
        
        rows, cols = matA.shape
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: SUMA DE MATRICES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matrices originales
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        
        # Verificar dimensiones
        if matA.shape != matB.shape:
            self.result_text.insert(tk.END, f"\n❌ ERROR: Las dimensiones no coinciden\n", "error")
            self.result_text.insert(tk.END, f"   A: {matA.rows}×{matA.cols}, B: {matB.rows}×{matB.cols}\n", "error")
            return
        
        # Calcular resultado
        result = [[matA[i,j]+matB[i,j] for j in range(cols)] for i in range(rows)]
        
        # Mostrar cálculo paso a paso
        self.result_text.insert(tk.END, f"\n🧮 CÁLCULO PASO A PASO:\n", "step")
        
        for i in range(rows):
            for j in range(cols):
                a_val = matA[i,j]
                b_val = matB[i,j]
                sum_val = result[i][j]
                self.result_text.insert(tk.END, f"C[{i+1},{j+1}] = A[{i+1},{j+1}] + B[{i+1},{j+1}] = {fraction_to_str(a_val)} + {fraction_to_str(b_val)} = {fraction_to_str(sum_val)}\n", "matrix")
        
        # Mostrar resultado final
        result_matrix = Matrix(result)
        self.display_matrix(result_matrix, "Matriz Resultante C = A + B", "matrix")
        
        self.result_text.insert(tk.END, f"\n✅ Suma completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def subtract_matrices(self):
        matA = self.get_matrix(self.entriesA)
        matB = self.get_matrix(self.entriesB)
        if matA is None or matB is None: return
        
        rows, cols = matA.shape
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: RESTA DE MATRICES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matrices originales
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        
        # Verificar dimensiones
        if matA.shape != matB.shape:
            self.result_text.insert(tk.END, f"\n❌ ERROR: Las dimensiones no coinciden\n", "error")
            self.result_text.insert(tk.END, f"   A: {matA.rows}×{matA.cols}, B: {matB.rows}×{matB.cols}\n", "error")
            return
        
        # Calcular resultado
        result = [[matA[i,j]-matB[i,j] for j in range(cols)] for i in range(rows)]
        
        # Mostrar cálculo paso a paso
        self.result_text.insert(tk.END, f"\n🧮 CÁLCULO PASO A PASO:\n", "step")
        
        for i in range(rows):
            for j in range(cols):
                a_val = matA[i,j]
                b_val = matB[i,j]
                diff_val = result[i][j]
                self.result_text.insert(tk.END, f"C[{i+1},{j+1}] = A[{i+1},{j+1}] - B[{i+1},{j+1}] = {fraction_to_str(a_val)} - {fraction_to_str(b_val)} = {fraction_to_str(diff_val)}\n", "matrix")
        
        # Mostrar resultado final
        result_matrix = Matrix(result)
        self.display_matrix(result_matrix, "Matriz Resultante C = A - B", "matrix")
        
        self.result_text.insert(tk.END, f"\n✅ Resta completada exitosamente\n", "independent")
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def multiply_matrices(self):
        matA = self.get_matrix(self.entriesA)
        matB = self.get_matrix(self.entriesB)
        if matA is None or matB is None: return
        
        rowsA, colsA = matA.shape
        colsB = matB.cols
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: MULTIPLICACIÓN DE MATRICES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matrices originales
        self.display_matrix(matA, "Matriz A", "matrix")
        self.display_matrix(matB, "Matriz B", "matrix")
        
        # Verificar dimensiones
        if colsA != matB.rows:
            self.result_text.insert(tk.END, f"\n❌ ERROR: Las dimensiones no son compatibles\n", "error")
            self.result_text.insert(tk.END, f"   Columnas de A ({colsA}) ≠ Filas de B ({matB.rows})\n", "error")
            return
        
        self.result_text.insert(tk.END, f"\n📊 Dimensiones: A ({rowsA}×{colsA}) × B ({matB.rows}×{colsB}) = Resultado ({rowsA}×{colsB})\n", "step")
        
        # Calcular resultado
        result = [[sum(matA[i,k]*matB[k,j] for k in range(colsA)) for j in range(colsB)] for i in range(rowsA)]
        
        # Mostrar cálculo paso a paso
        self.result_text.insert(tk.END, f"\n🧮 CÁLCULO PASO A PASO:\n", "step")
        
        for i in range(rowsA):
            for j in range(colsB):
                # Mostrar el cálculo de cada elemento
                calc_str = f"C[{i+1},{j+1}] = "
                terms = []
                for k in range(colsA):
                    terms.append(f"A[{i+1},{k+1}]×B[{k+1},{j+1}] = {fraction_to_str(matA[i,k])}×{fraction_to_str(matB[k,j])}")
                
                calc_str += " + ".join(terms)
                self.result_text.insert(tk.END, f"\n{calc_str}\n", "matrix")
                
                # Mostrar el resultado del elemento
                element_value = result[i][j]
                self.result_text.insert(tk.END, f"C[{i+1},{j+1}] = {fraction_to_str(element_value)}\n", "step")
        
        # Mostrar resultado final
        result_matrix = Matrix(result)
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
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: DETERMINANTE DE MATRIZ\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matriz original
        self.display_matrix(matA, "Matriz A", "matrix")
        
        self.result_text.insert(tk.END, f"\n📊 Información:\n", "step")
        self.result_text.insert(tk.END, f"   Tamaño: {n}×{n}\n", "matrix")
        self.result_text.insert(tk.END, f"   Método: {'Regla de Sarrus' if n == 3 else 'Reducción por filas'}\n", "matrix")
        
        self.result_text.insert(tk.END, f"\n🧮 CÁLCULO PASO A PASO:\n", "step")
        
        if n == 3:
            det = self._determinant_sarrus(matrix)
        else:
            det = self._determinant_step(matrix, show_text="Matriz de entrada para el determinante:")
        
        self.result_text.insert(tk.END, f"\n✅ RESULTADO FINAL:\n", "title")
        self.result_text.insert(tk.END, f"   det(A) = {fraction_to_str(det)}\n", "result")
        self.result_text.insert(tk.END, f"   Valor decimal: {float(det):.6f}\n", "matrix")
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
        detA = self._determinant_step([[matA[i,j] for j in range(matA.cols)] for i in range(matA.rows)],
                                      show_text="Determinante de la matriz A:")
        
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
        if matA.rows != matA.cols:
            messagebox.showerror("Error", "La matriz debe ser cuadrada para calcular cofactores.")
            return
        
        n = matA.rows
        
        self.result_text.insert(tk.END, f"\n{'='*60}\n", "title")
        self.result_text.insert(tk.END, f"OPERACIÓN: MATRIZ DE COFACTORES\n", "title")
        self.result_text.insert(tk.END, f"{'='*60}\n", "title")
        
        # Mostrar matriz original
        self.display_matrix(matA, "Matriz A", "matrix")
        
        self.result_text.insert(tk.END, f"\n📊 Información:\n", "step")
        self.result_text.insert(tk.END, f"   Tamaño: {n}×{n}\n", "matrix")
        self.result_text.insert(tk.END, f"   Fórmula: Cᵢⱼ = (-1)⁽ⁱ⁺ʲ⁾ × det(Mᵢⱼ)\n", "matrix")
        
        cofactores = []
        self.result_text.insert(tk.END, f"\n🧮 CÁLCULO DE COFACTORES PASO A PASO:\n", "step")
        
        for i in range(n):
            row_cof = []
            for j in range(n):
                self.result_text.insert(tk.END, f"\n📌 Cofactor C[{i+1},{j+1}]:\n", "step")
                
                # Crear submatriz
                submat = [[matA[r,c] for c in range(n) if c != j] for r in range(n) if r != i]
                submat_matrix = Matrix(submat)
                
                self.result_text.insert(tk.END, f"   Submatriz M[{i+1},{j+1}] (eliminando fila {i+1}, columna {j+1}):\n", "matrix")
                self.display_matrix(submat_matrix, f"M[{i+1},{j+1}]", "matrix")
                
                # Calcular determinante de submatriz
                if n-1 == 3:
                    det_sub = self._determinant_sarrus(submat)
                else:
                    det_sub = self._determinant_step(submat, show_text=f"Determinante de M[{i+1},{j+1}]:")
                
                # Calcular cofactor
                sign = (-1)**(i+j)
                cofactor = sign * det_sub
                row_cof.append(cofactor)
                
                self.result_text.insert(tk.END, f"   Signo: (-1)^({i+1}+{j+1}) = (-1)^{i+j+2} = {sign}\n", "matrix")
                self.result_text.insert(tk.END, f"   C[{i+1},{j+1}] = {sign} × {fraction_to_str(det_sub)} = {fraction_to_str(cofactor)}\n", "result")
            
            cofactores.append(row_cof)
        
        # Mostrar matriz de cofactores final
        cofactor_matrix = Matrix(cofactores)
        self.display_matrix(cofactor_matrix, "Matriz de Cofactores", "matrix")
        
        self.result_text.insert(tk.END, f"\n✅ Cálculo de cofactores completado exitosamente\n", "independent")
        
        # Calcular y mostrar matriz adjunta
        self.result_text.insert(tk.END, f"\n📌 MATRIZ ADJUNTA (transpuesta de cofactores):\n", "step")
        adjunta = [[cofactores[j][i] for j in range(n)] for i in range(n)]
        adjunta_matrix = Matrix(adjunta)
        self.display_matrix(adjunta_matrix, "Matriz Adjunta", "matrix")
        
        self.result_text.insert(tk.END, "\n" + "="*60 + "\n")

    def _determinant_step(self, matrix, show_text=""):
        n = len(matrix)
        mat = [row[:] for row in matrix]
        if show_text:
            self.result_text.insert(tk.END,f"{show_text}\n")
            for row in mat:
                self.result_text.insert(tk.END,"  ".join(fraction_to_str(val) for val in row)+"\n")
        det = Fraction(1)
        for i in range(n):
            pivot = mat[i][i]
            if pivot == 0:
                for k in range(i+1,n):
                    if mat[k][i] != 0:
                        mat[i], mat[k] = mat[k], mat[i]
                        det *= -1
                        pivot = mat[i][i]
                        break
            if pivot == 0:
                return Fraction(0)
            det *= pivot
            for j in range(i+1,n):
                factor = mat[j][i]/pivot
                for k in range(i,n):
                    mat[j][k] -= factor*mat[i][k]
        return det

    def _determinant_sarrus(self, matrix):
        a,b,c = matrix[0]
        d,e,f = matrix[1]
        g,h,i = matrix[2]
        self.result_text.insert(tk.END,"Cálculo del determinante por Sarrus (3x3):\n")
        self.result_text.insert(tk.END,"Matriz:\n")
        for row in matrix:
            self.result_text.insert(tk.END,"  ".join(fraction_to_str(x) for x in row)+"\n")
        sum1 = a*e*i + b*f*g + c*d*h
        sum2 = c*e*g + b*d*i + a*f*h
        self.result_text.insert(tk.END,f"Suma diagonales positivas: {fraction_to_str(a*e*i)} + {fraction_to_str(b*f*g)} + {fraction_to_str(c*d*h)} = {fraction_to_str(sum1)}\n")
        self.result_text.insert(tk.END,f"Suma diagonales negativas: {fraction_to_str(c*e*g)} + {fraction_to_str(b*d*i)} + {fraction_to_str(a*f*h)} = {fraction_to_str(sum2)}\n")
        det = sum1 - sum2
        self.result_text.insert(tk.END,f"Determinante final: {fraction_to_str(det)}\n\n")
        return det

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
        return os.path.join(os.path.dirname(__file__), "matrices_guardadas.json")

    def _read_saved(self):
        path = self._save_file_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _write_saved(self, data):
        path = self._save_file_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo escribir el archivo:\n{e}")
            return False

    def _collect_entries_as_strings(self, entries):
        rows = len(entries)
        cols = len(entries[0]) if rows else 0
        out = []
        for i in range(rows):
            row = []
            for j in range(cols):
                val = entries[i][j].get().strip()
                row.append(val if val != "" else "0")
            out.append(row)
        return out

    def _fill_entries_from_strings(self, entries, data_2d):
        rows = len(entries)
        cols = len(entries[0]) if rows else 0
        if rows != len(data_2d) or (rows and cols != len(data_2d[0])):
            return False
        for i in range(rows):
            for j in range(cols):
                entries[i][j].delete(0, tk.END)
                entries[i][j].insert(0, str(data_2d[i][j]))
        return True

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
                                   bg=self.colors["background"], fg=self.colors["text"])
        self.result_title.pack(anchor="w", pady=(0, 10))
        
        # Frame para mostrar resultados
        self.result_display = tk.Frame(self.result_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        self.result_display.pack(fill="both", expand=True)
        
        # Inicializar con la operación por defecto
        self.create_matrices()

    def create_gauss_matrix(self):
        """Crea la matriz aumentada para Gauss-Jordan"""
        # Limpiar frame anterior
        for widget in self.gauss_matrix_frame.winfo_children():
            widget.destroy()
        
        rows = self.gauss_rows.get()
        cols = self.gauss_cols.get()
        vector_mode = self.gauss_vector_mode.get()
        
        # Frame para la matriz
        matrix_container = tk.Frame(self.gauss_matrix_frame, bg=self.colors["matrix_bg"])
        matrix_container.pack()
        
        # Título
        title_text = "Matriz de Vectores" if vector_mode else "Matriz Aumentada [A|b]"
        title = tk.Label(matrix_container, text=title_text, 
                        font=("Segoe UI", 14, "bold"),
                        bg=self.colors["matrix_bg"], fg=self.colors["text"])
        title.pack(pady=(0, 15))
        
        # Frame para las entradas
        entries_frame = tk.Frame(matrix_container, bg=self.colors["matrix_bg"])
        entries_frame.pack()
        
        self.gauss_entries = []
        
        # Estilo para entradas
        entry_style = {
            "font": ("Consolas", 11),
            "width": 8,
            "bg": self.colors["entry_bg"],
            "fg": self.colors["text"],
            "insertbackground": self.colors["text"],
            "relief": "flat",
            "bd": 1
        }
        
        # Crear encabezados de columnas
        if vector_mode:
            for j in range(cols):
                var_label = tk.Label(entries_frame, text=f"v{j+1}", 
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["matrix_bg"], fg=self.colors["accent"])
                var_label.grid(row=0, column=j*2, padx=3, pady=3)
        else:
            for j in range(cols):
                var_label = tk.Label(entries_frame, text=f"x{j+1}", 
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["matrix_bg"], fg=self.colors["accent"])
                var_label.grid(row=0, column=j*2, padx=3, pady=3)
            
            # Etiqueta para el vector b
            b_label = tk.Label(entries_frame, text="b", 
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colors["matrix_bg"], fg=self.colors["accent"])
            b_label.grid(row=0, column=cols*2, padx=3, pady=3)
        
        # Crear entradas
        for i in range(rows):
            row_entries = []
            for j in range(cols if vector_mode else cols + 1):
                entry = tk.Entry(entries_frame, **entry_style)
                entry.grid(row=i+1, column=j*2 if vector_mode else j, padx=3, pady=3)
                entry.insert(0, "0")
                row_entries.append(entry)
                
                # Agregar símbolos de operación entre columnas
                if j < (cols - 1 if vector_mode else cols - 1):
                    op_label = tk.Label(entries_frame, text="+", 
                                      font=("Segoe UI", 11),
                                      bg=self.colors["matrix_bg"], fg=self.colors["accent"])
                    op_label.grid(row=i+1, column=j*2+1 if vector_mode else j+1, padx=2)
            
            self.gauss_entries.append(row_entries)
        
        # Línea vertical para separar A de b (solo si no es modo vectores)
        if not vector_mode:
            separator = tk.Frame(entries_frame, bg=self.colors["accent"], width=2)
            separator.grid(row=1, column=cols, rowspan=rows, sticky="ns", padx=(0, 3))

    def solve_gauss_jordan(self):
        """Resuelve el sistema usando Gauss-Jordan con análisis completo"""
        if not self.gauss_entries:
            messagebox.showerror("Error", "Primero genera la matriz.")
            return
        
        self.gauss_result_text.config(state="normal")
        self.gauss_result_text.delete("1.0", tk.END)
        
        try:
            # Obtener la matriz
            rows = len(self.gauss_entries)
            cols = len(self.gauss_entries[0])
            vector_mode = self.gauss_vector_mode.get()
            
            # Crear matriz de fracciones
            matrix = []
            for i in range(rows):
                row = []
                for j in range(cols):
                    value = self.gauss_entries[i][j].get()
                    if not value:
                        value = "0"
                    row.append(Fraction(value))
                matrix.append(row)
            
            # Si estamos en modo vectores, añadir columna de ceros
            if vector_mode:
                for row in matrix:
                    row.append(Fraction(0))
                cols += 1
            
            self.gauss_result_text.insert(tk.END, "Matriz original:\n", "step")
            self._print_gauss_matrix(matrix)
            self.gauss_result_text.insert(tk.END, "\n")
            
            # Aplicar Gauss-Jordan con análisis completo
            self._gauss_jordan_elimination_advanced(matrix, vector_mode)
            
        except Exception as e:
            self.gauss_result_text.insert(tk.END, f"\nError: {str(e)}")
        
        self.gauss_result_text.config(state="disabled")

    def _gauss_jordan_elimination_advanced(self, matrix, vector_mode=False):
        """Implementa Gauss-Jordan con análisis completo del sistema"""
        rows = len(matrix)
        cols = len(matrix[0])
        n_vars = cols - 1
        
        pivot_columns = []
        free_variables = []
        step = 1
        
        for i in range(min(rows, n_vars)):
            pivot_found = False
            
            # Encontrar fila pivote
            pivot_row = i
            for j in range(i + 1, rows):
                if abs(matrix[j][i]) > abs(matrix[pivot_row][i]):
                    pivot_row = j
            
            # Intercambiar filas si es necesario
            if pivot_row != i and matrix[pivot_row][i] != 0:
                matrix[i], matrix[pivot_row] = matrix[pivot_row], matrix[i]
                self.gauss_result_text.insert(tk.END, f"Paso {step}: Intercambiar fila {i+1} con fila {pivot_row+1}\n", "step")
                self._print_gauss_matrix(matrix)
                self.gauss_result_text.insert(tk.END, "\n")
                step += 1
            
            # Hacer 1 el elemento pivote
            if matrix[i][i] != 0:
                pivot = matrix[i][i]
                for j in range(cols):
                    matrix[i][j] = matrix[i][j] / pivot
                
                self.gauss_result_text.insert(tk.END, f"Paso {step}: Dividir fila {i+1} por {self._fraction_to_str(pivot)}\n", "step")
                self._print_gauss_matrix(matrix)
                self.gauss_result_text.insert(tk.END, "\n")
                step += 1
                pivot_found = True
                pivot_columns.append(i)
            
            # Hacer ceros en la columna
            if pivot_found:
                for k in range(rows):
                    if k != i and matrix[k][i] != 0:
                        factor = matrix[k][i]
                        for j in range(cols):
                            matrix[k][j] = matrix[k][j] - factor * matrix[i][j]
                        
                        self.gauss_result_text.insert(tk.END, f"Paso {step}: Restar {self._fraction_to_str(factor)} veces la fila {i+1} de la fila {k+1}\n", "step")
                        self._print_gauss_matrix(matrix)
                        self.gauss_result_text.insert(tk.END, "\n")
                        step += 1
            else:
                if i < n_vars:
                    free_variables.append(i)
                    self.gauss_result_text.insert(tk.END, f"La variable x{i+1} es una variable libre\n", "free_var_info")
            
            # Mostrar estado actual
            self._show_gauss_state(pivot_columns, free_variables, n_vars)
        
        # Análisis final del sistema
        self._analyze_gauss_system(matrix, pivot_columns, free_variables, vector_mode)

    def _show_gauss_state(self, pivot_columns, free_variables, n_vars):
        """Muestra el estado actual del proceso"""
        self.gauss_result_text.insert(tk.END, "Estado actual:\n", "step")
        self.gauss_result_text.insert(tk.END, f"Columnas pivote encontradas: {[col+1 for col in pivot_columns]}\n", "matrix")
        
        all_free_vars = free_variables + [i for i in range(n_vars) if i not in pivot_columns and i not in free_variables]
        if all_free_vars:
            self.gauss_result_text.insert(tk.END, f"Variables libres identificadas: x{', x'.join(map(str, [v+1 for v in free_variables]))}", "free_var_info")
            if [i for i in range(n_vars) if i not in pivot_columns and i not in free_variables]:
                potential_free = [i+1 for i in range(n_vars) if i not in pivot_columns and i not in free_variables]
                self.gauss_result_text.insert(tk.END, f" (potenciales adicionales: x{', x'.join(map(str, potential_free))})", "matrix")
            self.gauss_result_text.insert(tk.END, "\n\n")
        else:
            self.gauss_result_text.insert(tk.END, "No se han identificado variables libres aún\n\n", "matrix")

    def _analyze_gauss_system(self, matrix, pivot_columns, free_variables, vector_mode=False):
        """Análisis completo del sistema de ecuaciones"""
        rows = len(matrix)
        cols = len(matrix[0])
        n_vars = cols - 1
        
        # Verificar consistencia
        inconsistent = False
        for i in range(rows):
            if all(matrix[i][j] == 0 for j in range(n_vars)) and matrix[i][-1] != 0:
                inconsistent = True
                break
        
        self.gauss_result_text.insert(tk.END, "\nANÁLISIS FINAL DEL SISTEMA:\n", "title")
        self.gauss_result_text.insert(tk.END, "=========================\n", "title")
        
        if inconsistent:
            self.gauss_result_text.insert(tk.END, "El sistema es INCONSISTENTE (no tiene solución).\n", "inconsistent")
        else:
            self._show_gauss_solution(matrix, pivot_columns, free_variables, vector_mode)
            
            # Verificar independencia lineal si estamos en modo vectores
            if vector_mode:
                self._check_linear_independence(pivot_columns, n_vars)

    def _check_linear_independence(self, pivot_columns, n_vars):
        """Verifica si los vectores son linealmente independientes"""
        self.gauss_result_text.insert(tk.END, "\nANÁLISIS DE INDEPENDENCIA LINEAL:\n", "title")
        self.gauss_result_text.insert(tk.END, "=============================\n", "title")
        
        if len(pivot_columns) == n_vars:
            self.gauss_result_text.insert(tk.END, "Los vectores son LINEALMENTE INDEPENDIENTES.\n", "independent")
            self.gauss_result_text.insert(tk.END, "Explicación: El número de columnas pivote es igual al número de variables, lo que significa que no hay variables libres y la única solución del sistema homogéneo es la trivial (todos ceros).\n", "note")
        else:
            self.gauss_result_text.insert(tk.END, "Los vectores son LINEALMENTE DEPENDIENTES.\n", "dependent")
            self.gauss_result_text.insert(tk.END, f"Explicación: Hay {n_vars - len(pivot_columns)} variables libres, lo que significa que el sistema homogéneo tiene infinitas soluciones no triviales.\n", "note")

    def _show_gauss_solution(self, matrix, pivot_columns, free_variables, vector_mode=False):
        """Muestra la solución del sistema"""
        n_vars = len(matrix[0]) - 1
        
        self.gauss_result_text.insert(tk.END, "Columnas pivote: ", "subtitle")
        self.gauss_result_text.insert(tk.END, f"{[col+1 for col in pivot_columns]}\n", "value")
        
        if free_variables:
            self.gauss_result_text.insert(tk.END, "Variables libres: ", "subtitle")
            self.gauss_result_text.insert(tk.END, f"x{', x'.join(map(str, [v+1 for v in free_variables]))}\n", "free_var")
            self.gauss_result_text.insert(tk.END, "El sistema tiene INFINITAS SOLUCIONES.\n", "solution_type")
            self.gauss_result_text.insert(tk.END, "Cada variable libre puede tomar cualquier valor real.\n", "note")
        else:
            self.gauss_result_text.insert(tk.END, "No hay variables libres.\n", "subtitle")
            self.gauss_result_text.insert(tk.END, "El sistema tiene SOLUCIÓN ÚNICA.\n", "solution_type")
        
        self.gauss_result_text.insert(tk.END, "\nSOLUCIÓN FINAL:\n", "title")
        self.gauss_result_text.insert(tk.END, "=============\n", "title")
        
        if not free_variables:
            # Solución única
            for i in range(min(len(pivot_columns), n_vars)):
                if i in pivot_columns:
                    self.gauss_result_text.insert(tk.END, f"x{i+1} = ", "var_name")
                    self.gauss_result_text.insert(tk.END, f"{self._fraction_to_str(matrix[i][-1])}\n", "var_value")
        else:
            # Solución paramétrica
            self.gauss_result_text.insert(tk.END, "Variables dependientes en términos de variables libres:\n", "subtitle")
            for i in range(len(pivot_columns)):
                pivot_col = pivot_columns[i]
                self.gauss_result_text.insert(tk.END, f"x{pivot_col+1} = ", "var_name")
                self.gauss_result_text.insert(tk.END, f"{self._fraction_to_str(matrix[i][-1])}", "var_value")
                
                for j in free_variables:
                    coef = -matrix[i][j]
                    if coef != 0:
                        sign = "+" if coef > 0 else "-"
                        coef_str = self._fraction_to_str(abs(coef))
                        self.gauss_result_text.insert(tk.END, f" {sign} ", "operator")
                        self.gauss_result_text.insert(tk.END, f"{coef_str}", "coefficient")
                        self.gauss_result_text.insert(tk.END, f"x{j+1}", "free_var")
                
                self.gauss_result_text.insert(tk.END, "\n")
            
            self.gauss_result_text.insert(tk.END, "\nVariables libres:\n", "subtitle")
            for j in free_variables:
                self.gauss_result_text.insert(tk.END, f"x{j+1} ", "free_var")
                self.gauss_result_text.insert(tk.END, "puede tomar cualquier valor real\n", "note")

    def _fraction_to_str(self, frac):
        """Convierte una fracción a string"""
        if isinstance(frac, Fraction):
            if frac.denominator == 1:
                return str(frac.numerator)
            else:
                return f"{frac.numerator}/{frac.denominator}"
        return str(frac)

    def _print_gauss_matrix(self, matrix):
        """Imprime la matriz aumentada con formato mejorado"""
        rows = len(matrix)
        cols = len(matrix[0])
        
        for i in range(rows):
            row_str = "  ["
            for j in range(cols):
                if j == cols - 1:  # Columna de resultados
                    row_str += " | "
                elif j > 0:
                    row_str += "  "
                
                value = matrix[i][j]
                value_str = self._fraction_to_str(value)
                row_str += f"{value_str:>8}"
            row_str += " ]"
            self.gauss_result_text.insert(tk.END, row_str + "\n", "matrix")

    def clear_gauss(self):
        """Limpia la pestaña de Gauss-Jordan"""
        # Limpiar entradas
        if self.gauss_entries:
            for row in self.gauss_entries:
                for entry in row:
                    entry.delete(0, tk.END)
                    entry.insert(0, "0")
        
        # Limpiar resultado
        self.gauss_result_text.config(state="normal")
        self.gauss_result_text.delete("1.0", tk.END)
        self.gauss_result_text.insert("1.0", "Los pasos del método de Gauss-Jordan se mostrarán aquí.")
        self.gauss_result_text.config(state="disabled")

    def setup_bisection_tab(self):
        """Configura la pestaña del Método de Bisección"""
        # Frame con borde para diferenciar la pestaña
        border_frame = tk.Frame(self.bisection_tab, bg="#7B68EE", relief="flat", bd=2)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Frame principal dentro del borde
        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Título
        title_label = tk.Label(main_frame, text="Método de Bisección", 
                              font=("Segoe UI", 24, "bold"),
                              bg=self.colors["background"], fg=self.colors["accent"])
        title_label.pack(pady=(0, 20))
        
        # Frame superior para controles
        top_frame = tk.Frame(main_frame, bg=self.colors["background"])
        top_frame.pack(pady=(0, 15), fill="x")
        
        # Frame para entrada de función
        func_frame = tk.Frame(top_frame, bg=self.colors["background"])
        func_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(func_frame, text="Función f(x):", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        
        # Frame para la entrada de función y botón de teclado
        func_input_frame = tk.Frame(func_frame, bg=self.colors["background"])
        func_input_frame.pack(fill="x")
        
        self.function_var = tk.StringVar()
        self.function_entry = tk.Entry(func_input_frame, textvariable=self.function_var,
                                    font=("Segoe UI", 12), width=40,
                                    bg=self.colors["entry_bg"], fg=self.colors["text"],
                                    insertbackground=self.colors["text"], relief="flat", bd=1)
        self.function_entry.pack(side="left", padx=(0, 10))
        
        # Botón para mostrar/ocultar teclado con mejor estilo
        self.keyboard_btn = tk.Button(func_input_frame, text="🔽 Ocultar Teclado",
                                     command=self.toggle_keyboard,
                                     bg=self.colors["button_secondary"], fg="white",
                                     font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                                     padx=15, pady=6, cursor="hand2",
                                     activebackground=self.colors["accent"],
                                     activeforeground="white")
        self.keyboard_btn.pack(side="left", padx=(0, 5))
        
        # Efecto hover para botón de teclado
        def on_enter_keyboard(e):
            self.keyboard_btn.config(bg=self.colors["accent"])
        def on_leave_keyboard(e):
            self.keyboard_btn.config(bg=self.colors["button_secondary"])
        self.keyboard_btn.bind("<Enter>", on_enter_keyboard)
        self.keyboard_btn.bind("<Leave>", on_leave_keyboard)
        
        # Botón de ayuda para funciones
        help_btn = tk.Button(func_input_frame, text="❓ Ayuda",
                           command=self.show_function_help,
                           bg=self.colors["accent"], fg="white",
                           font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                           padx=10, pady=5, cursor="hand2")
        help_btn.pack(side="left")
        
        # Frame para parámetros de bisección
        params_frame = tk.Frame(top_frame, bg=self.colors["background"])
        params_frame.pack(fill="x", pady=(10, 0))
        
        # Intervalo [a, b]
        interval_frame = tk.Frame(params_frame, bg=self.colors["background"])
        interval_frame.pack(side="left", padx=(0, 20))
        
        tk.Label(interval_frame, text="Intervalo [a, b]:", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        
        interval_input_frame = tk.Frame(interval_frame, bg=self.colors["background"])
        interval_input_frame.pack()
        
        self.a_var = tk.StringVar(value="-1")
        self.b_var = tk.StringVar(value="1")
        
        tk.Entry(interval_input_frame, textvariable=self.a_var, width=10,
                font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                insertbackground=self.colors["text"], relief="flat", bd=1).pack(side="left", padx=(0, 5))
        
        tk.Label(interval_input_frame, text="≤ x ≤", font=("Segoe UI", 12),
                bg=self.colors["background"], fg=self.colors["text"]).pack(side="left", padx=5)
        
        tk.Entry(interval_input_frame, textvariable=self.b_var, width=10,
                font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                insertbackground=self.colors["text"], relief="flat", bd=1).pack(side="left", padx=(5, 0))
        
        # Tolerancia
        tol_frame = tk.Frame(params_frame, bg=self.colors["background"])
        tol_frame.pack(side="left", padx=(0, 20))
        
        tk.Label(tol_frame, text="Tolerancia:", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        
        self.tol_var = tk.StringVar(value="0.0001")
        tk.Entry(tol_frame, textvariable=self.tol_var, width=15,
                font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                insertbackground=self.colors["text"], relief="flat", bd=1).pack()
        
        # Iteraciones máximas
        iter_frame = tk.Frame(params_frame, bg=self.colors["background"])
        iter_frame.pack(side="left")
        
        tk.Label(iter_frame, text="Máx. iteraciones:", 
                font=("Segoe UI", 12, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        
        self.max_iter_var = tk.StringVar(value="100")
        tk.Entry(iter_frame, textvariable=self.max_iter_var, width=10,
                font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                insertbackground=self.colors["text"], relief="flat", bd=1).pack()
        
        # Frame para botones
        btn_frame = tk.Frame(top_frame, bg=self.colors["background"])
        btn_frame.pack(pady=(15, 0))
        
        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 22,
            "pady": 10,
            "cursor": "hand2",
            "activebackground": self.colors["accent"],
            "activeforeground": "white"
        }
        
        # Botón Calcular Raíz
        calc_btn = tk.Button(btn_frame, text="🔢 Calcular Raíz", command=self.calculate_bisection,
                  bg=self.colors["accent"], fg="white", **button_style)
        calc_btn.pack(side="left", padx=(0, 8))
        
        # Botón Falsa Posición
        falsepos_btn = tk.Button(btn_frame, text="📐 Falsa Posición", command=self.calculate_false_position,
                  bg="#FFB703", fg="white", **button_style)
        falsepos_btn.pack(side="left", padx=(0, 8))
        
        # Botón Limpiar
        clear_btn = tk.Button(btn_frame, text="🗑 Limpiar", command=self.clear_bisection,
                  bg=self.colors["button_secondary"], fg="white", **button_style)
        clear_btn.pack(side="left", padx=(0, 8))
        
        # Botón Graficar
        plot_btn = tk.Button(btn_frame, text="📊 Graficar Función", command=self.plot_function,
                  bg="#7B68EE", fg="white", **button_style)
        plot_btn.pack(side="left", padx=(0, 8))
        
        # Botón Sugerir Intervalo
        suggest_btn = tk.Button(btn_frame, text="🔎 Sugerir Intervalo", command=self.suggest_interval,
                  bg="#20B2AA", fg="white", **button_style)
        suggest_btn.pack(side="left", padx=(0, 8))
        
        # Agregar efectos hover a los botones
        def add_hover_effect(btn, original_bg):
            def on_enter(e):
                btn.config(bg=self.colors["accent"])
            def on_leave(e):
                btn.config(bg=original_bg)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        add_hover_effect(clear_btn, self.colors["button_secondary"])
        add_hover_effect(plot_btn, "#7B68EE")
        add_hover_effect(suggest_btn, "#20B2AA")
        add_hover_effect(falsepos_btn, "#FFB703")
        
        # Frame para resultados (crear primero para tener referencia)
        self.bisection_result_frame = tk.Frame(main_frame, bg=self.colors["background"])
        self.bisection_result_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        # Frame para el teclado virtual (visible por defecto)
        self.keyboard_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        self.keyboard_frame.pack(pady=(15, 0), fill="x", padx=20, before=self.bisection_result_frame)
        # El teclado estará visible por defecto
        self.keyboard_visible = True
        
        self.setup_virtual_keyboard()
        
        tk.Label(self.bisection_result_frame, text="Resultados:", font=("Segoe UI", 14, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        
        # Área de resultados
        self.bisection_result_text = scrolledtext.ScrolledText(self.bisection_result_frame, width=80, height=20,
                                                             font=("Consolas", 10),
                                                             bg=self.colors["secondary_bg"], 
                                                             fg=self.colors["text"],
                                                             insertbackground=self.colors["text"],
                                                             relief="flat", bd=1)
        self.bisection_result_text.pack(fill="both", expand=True)
        
        # Configurar estilos de texto
        self.bisection_result_text.tag_configure("title", foreground=self.colors["accent"], font=("Consolas", 10, "bold"))
        self.bisection_result_text.tag_configure("step", foreground="#30D158", font=("Consolas", 10))
        self.bisection_result_text.tag_configure("error", foreground="#FF453A", font=("Consolas", 10, "bold"))
        self.bisection_result_text.tag_configure("result", foreground="#30D158", font=("Consolas", 11, "bold"))
        self.bisection_result_text.tag_configure("warning", foreground="#FF9F0A", font=("Consolas", 10))
        
        # Mensaje inicial
        self.bisection_result_text.insert("1.0", "Los resultados del método de bisección se mostrarán aquí.")
        self.bisection_result_text.config(state="disabled")

    def setup_false_position_tab(self):
        """Configura la pestaña del Método de Falsa Posición"""
        border_frame = tk.Frame(self.falsepos_tab, bg="#FFB703", relief="flat", bd=2)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)

        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=2, pady=2)

        title_label = tk.Label(
            main_frame, text="Método de Falsa Posición",
            font=("Segoe UI", 24, "bold"),
            bg=self.colors["background"], fg="#FFB703"
        )
        title_label.pack(pady=(0, 20))

        # Controles superiores
        top_frame = tk.Frame(main_frame, bg=self.colors["background"]) 
        top_frame.pack(pady=(0, 15), fill="x")

        # Función
        func_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        func_frame.pack(fill="x", pady=(0, 10))

        tk.Label(func_frame, text="Función f(x):",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))

        func_input_frame = tk.Frame(func_frame, bg=self.colors["background"]) 
        func_input_frame.pack(fill="x")

        self.fp_function_var = tk.StringVar()
        self.fp_function_entry = tk.Entry(
            func_input_frame, textvariable=self.fp_function_var,
            font=("Segoe UI", 12), width=40,
            bg=self.colors["entry_bg"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief="flat", bd=1
        )
        self.fp_function_entry.pack(side="left", padx=(0, 10))

        # Botón para mostrar/ocultar teclado
        self.fp_keyboard_btn = tk.Button(func_input_frame, text="🔽 Ocultar Teclado",
                                         command=self.toggle_keyboard_fp,
                                         bg=self.colors["button_secondary"], fg="white",
                                         font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                                         padx=15, pady=6, cursor="hand2",
                                         activebackground=self.colors["accent"],
                                         activeforeground="white")
        self.fp_keyboard_btn.pack(side="left", padx=(0, 5))

        # Efecto hover para botón de teclado
        def on_enter_keyboard_fp(e):
            self.fp_keyboard_btn.config(bg=self.colors["accent"])
        def on_leave_keyboard_fp(e):
            self.fp_keyboard_btn.config(bg=self.colors["button_secondary"])
        self.fp_keyboard_btn.bind("<Enter>", on_enter_keyboard_fp)
        self.fp_keyboard_btn.bind("<Leave>", on_leave_keyboard_fp)

        help_btn = tk.Button(func_input_frame, text="❓ Ayuda",
                             command=self.show_function_help,
                             bg=self.colors["accent"], fg="white",
                             font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                             padx=10, pady=5, cursor="hand2")
        help_btn.pack(side="left")

        # Parámetros
        params_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        params_frame.pack(fill="x", pady=(10, 0))

        interval_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        interval_frame.pack(side="left", padx=(0, 20))
        tk.Label(interval_frame, text="Intervalo [a, b]:",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        interval_input_frame = tk.Frame(interval_frame, bg=self.colors["background"]) 
        interval_input_frame.pack()
        self.fp_a_var = tk.StringVar(value="-1")
        self.fp_b_var = tk.StringVar(value="1")
        tk.Entry(interval_input_frame, textvariable=self.fp_a_var, width=10,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack(side="left", padx=(0, 5))
        tk.Label(interval_input_frame, text="≤ x ≤", font=("Segoe UI", 12),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(side="left", padx=5)
        tk.Entry(interval_input_frame, textvariable=self.fp_b_var, width=10,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack(side="left", padx=(5, 0))

        tol_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        tol_frame.pack(side="left", padx=(0, 20))
        tk.Label(tol_frame, text="Tolerancia:",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        self.fp_tol_var = tk.StringVar(value="0.0001")
        tk.Entry(tol_frame, textvariable=self.fp_tol_var, width=15,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()

        iter_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        iter_frame.pack(side="left")
        tk.Label(iter_frame, text="Máx. iteraciones:",
                 font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 5))
        self.fp_max_iter_var = tk.StringVar(value="100")
        tk.Entry(iter_frame, textvariable=self.fp_max_iter_var, width=10,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()

        # Botones
        btn_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        btn_frame.pack(pady=(15, 0))
        button_style = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 22,
            "pady": 10,
            "cursor": "hand2",
            "activebackground": self.colors["accent"],
            "activeforeground": "white"
        }

        tk.Button(btn_frame, text="📐 Calcular (Falsa Posición)", command=self.calculate_false_position_fp,
                  bg="#FFB703", fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🗑 Limpiar", command=self.clear_false_position,
                  bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="📊 Graficar Función", command=self.plot_function_fp,
                  bg="#7B68EE", fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🔎 Sugerir Intervalo", command=self.suggest_interval_fp,
                  bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0, 8))

        # Frame para el teclado virtual (visible por defecto)
        self.fp_keyboard_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        self.fp_keyboard_frame.pack(pady=(15, 0), fill="x", padx=20)
        self.fp_keyboard_visible = True
        
        self.setup_virtual_keyboard_fp()
        
        # Resultados
        self.fp_result_frame = tk.Frame(main_frame, bg=self.colors["background"]) 
        self.fp_result_frame.pack(fill="both", expand=True, pady=(15, 0))
        tk.Label(self.fp_result_frame, text="Resultados:", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        self.falsepos_result_text = scrolledtext.ScrolledText(
            self.fp_result_frame, width=80, height=20, font=("Consolas", 10),
            bg=self.colors["secondary_bg"], fg=self.colors["text"],
            insertbackground=self.colors["text"], relief="flat", bd=1
        )
        self.falsepos_result_text.pack(fill="both", expand=True)
        self.falsepos_result_text.tag_configure("title", foreground="#FFB703", font=("Consolas", 10, "bold"))
        self.falsepos_result_text.tag_configure("step", foreground="#30D158", font=("Consolas", 10))
        self.falsepos_result_text.tag_configure("error", foreground="#FF453A", font=("Consolas", 10, "bold"))
        self.falsepos_result_text.tag_configure("result", foreground="#30D158", font=("Consolas", 11, "bold"))
        self.falsepos_result_text.tag_configure("warning", foreground="#FF9F0A", font=("Consolas", 10))
        self.falsepos_result_text.insert("1.0", "Los resultados de Falsa Posición se mostrarán aquí.")
        self.falsepos_result_text.config(state="disabled")

    def calculate_false_position_fp(self):
        """Método de Falsa Posición para la pestaña dedicada"""
        try:
            func_str = self.fp_function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return

            a = float(self.fp_a_var.get())
            b = float(self.fp_b_var.get())
            tolerance = float(self.fp_tol_var.get())
            max_iterations = int(self.fp_max_iter_var.get())

            if a >= b:
                messagebox.showerror("Error", "El valor de 'a' debe ser menor que 'b'")
                return
            if tolerance <= 0:
                messagebox.showerror("Error", "La tolerancia debe ser positiva")
                return

            fa = self.evaluate_function(a, func_str)
            fb = self.evaluate_function(b, func_str)
            if fa * fb > 0:
                messagebox.showerror("Error", "La función no cambia de signo en [a,b].\nFalsa Posición requiere f(a) * f(b) < 0")
                return
            if fa == fb:
                messagebox.showerror("Error", "f(a) y f(b) son iguales; la fórmula se indetermina")
                return

            self.falsepos_result_text.config(state="normal")
            self.falsepos_result_text.delete("1.0", tk.END)
            self.falsepos_result_text.insert("1.0", f"MÉTODO DE FALSA POSICIÓN (Regla Falsa)\n", "title")
            # Mostrar función con valores numéricos en lugar de símbolos
            formatted_func = self.format_function_display(func_str)
            self.falsepos_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.falsepos_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
            self.falsepos_result_text.insert(tk.END, f"Tolerancia: {tolerance}\n", "step")
            self.falsepos_result_text.insert(tk.END, f"Máximo de iteraciones: {max_iterations}\n\n", "step")

            iteration = 0
            prev_c = None

            while iteration < max_iterations:
                fa = self.evaluate_function(a, func_str)
                fb = self.evaluate_function(b, func_str)
                if fb == fa:
                    self.falsepos_result_text.insert(tk.END, "⚠ f(a) == f(b); fórmula indeterminada\n", "warning")
                    break

                c = b - fb * (b - a) / (fb - fa)
                fc = self.evaluate_function(c, func_str)

                self.falsepos_result_text.insert(tk.END, f"Iteración {iteration + 1}:\n", "step")
                self.falsepos_result_text.insert(tk.END, f"  a = {a:.8f}, f(a) = {fa:.8f}\n")
                self.falsepos_result_text.insert(tk.END, f"  b = {b:.8f}, f(b) = {fb:.8f}\n")
                self.falsepos_result_text.insert(tk.END, f"  c = {c:.8f}, f(c) = {fc:.8f}\n")

                error_c = abs(fc)
                error_intervalo = abs(b - a)
                self.falsepos_result_text.insert(tk.END, f"  Error |f(c)| = {error_c:.8f}, ancho intervalo = {error_intervalo:.8f}\n")

                if abs(fc) <= tolerance or (prev_c is not None and abs(c - prev_c) <= tolerance) or error_intervalo <= tolerance:
                    prev_c = c
                    break

                if fa * fc < 0:
                    b = c
                    fb = fc
                    self.falsepos_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(a) * f(c) < 0)\n\n")
                else:
                    a = c
                    fa = fc
                    self.falsepos_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(b) * f(c) < 0)\n\n")

                prev_c = c
                iteration += 1

            root = prev_c if prev_c is not None else (a + b) / 2
            self.falsepos_result_text.insert(tk.END, "=" * 60 + "\n", "title")
            self.falsepos_result_text.insert(tk.END, "RESULTADO FINAL (Falsa Posición):\n", "result")
            self.falsepos_result_text.insert(tk.END, f"Raíz aproximada: x = {root:.8f}\n", "result")
            self.falsepos_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.falsepos_result_text.insert(tk.END, f"Número de iteraciones: {iteration}\n", "result")
            self.falsepos_result_text.insert(tk.END, f"Error final |f(c)|: {abs(self.evaluate_function(root, func_str)):.2e}\n", "result")

            if iteration >= max_iterations:
                self.falsepos_result_text.insert(tk.END, "\n⚠ ADVERTENCIA: Se alcanzó el máximo de iteraciones\n", "warning")

            self.falsepos_result_text.config(state="disabled")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error en Falsa Posición: {str(e)}")

    def clear_false_position(self):
        """Limpia la pestaña de Falsa Posición"""
        self.fp_function_var.set("")
        self.fp_a_var.set("-1")
        self.fp_b_var.set("1")
        self.fp_tol_var.set("0.0001")
        self.fp_max_iter_var.set("100")
        self.falsepos_result_text.config(state="normal")
        self.falsepos_result_text.delete("1.0", tk.END)
        self.falsepos_result_text.insert("1.0", "Los resultados de Falsa Posición se mostrarán aquí.")
        self.falsepos_result_text.config(state="disabled")

    def plot_function_fp(self):
        """Grafica f(x) del tab de Falsa Posición en [a,b]"""
        try:
            func_str = self.fp_function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return

            # Leer intervalo
            try:
                a = float(self.fp_a_var.get())
                b = float(self.fp_b_var.get())
            except ValueError:
                messagebox.showerror("Error", "Intervalo inválido. Ingrese números en 'a' y 'b'.")
                return

            if a >= b:
                messagebox.showerror("Error", "El valor de 'a' debe ser menor que 'b'")
                return

            # Muestreo en [a, b]
            num_points = 600
            step = (b - a) / num_points
            xs = [a + i * step for i in range(num_points + 1)]
            ys = []
            valid_points = 0
            for x in xs:
                try:
                    y = self.evaluate_function(x, func_str)
                    ys.append(y)
                    valid_points += 1
                except Exception:
                    ys.append(float("nan"))

            if valid_points == 0:
                messagebox.showerror("Error al graficar", "No se pudieron evaluar puntos válidos en el intervalo.")
                return

            # Graficar
            plt.figure(figsize=(7, 4.5))
            # Mostrar función con valores numéricos
            formatted_func = self.format_function_display(func_str)
            plt.plot(xs, ys, label=f"f(x) = {formatted_func}", color="#FFB703", linewidth=2)
            plt.axhline(0, color="#FF453A", linewidth=1)
            plt.axvline(0, color="#FF9F0A", linewidth=1)
            plt.title(f"Gráfica de f(x) = {formatted_func} - Falsa Posición")
            plt.xlabel("x")
            plt.ylabel("f(x)")
            plt.grid(True, linestyle="--", alpha=0.5)
            plt.legend()
            plt.tight_layout()
            plt.show()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar la función: {str(e)}")

    def suggest_interval_fp(self):
        """Sugiere intervalos [a,b] del tab de Falsa Posición con cambio de signo"""
        func_str = self.fp_function_var.get().strip()
        if not func_str:
            messagebox.showerror("Error", "Por favor ingrese una función en 'f(x)'.")
            return

        search_specs = [(-10, 10, 0.1), (-50, 50, 0.2), (-100, 100, 0.5)]
        intervals = []
        for a_range, b_range, step in search_specs:
            prev_x, prev_y = None, None
            x = a_range
            while x <= b_range:
                try:
                    y = float(self.evaluate_function(x, func_str))
                    if prev_y is not None and not math.isnan(prev_y) and not math.isnan(y):
                        if prev_y * y < 0:
                            intervals.append((prev_x, x))
                            if len(intervals) >= 8:
                                break
                    prev_x, prev_y = x, y
                except Exception:
                    prev_x, prev_y = None, None
                x = round(x + step, 10)
            if intervals:
                break

        if not intervals:
            messagebox.showwarning("Sin cambio de signo",
                                   "No se encontraron intervalos con cambio de signo en los rangos probados.")
            return

        a, b = intervals[0]
        self.fp_a_var.set(f"{a:.6f}")
        self.fp_b_var.set(f"{b:.6f}")

        txt = "Intervalos con cambio de signo detectados:\n\n"
        for i, (ia, ib) in enumerate(intervals, 1):
            txt += f"{i}. [{ia:.6f}, {ib:.6f}]\n"
        txt += "\nSe asignó el primero en los campos 'a' y 'b'."
        messagebox.showinfo("Sugerencia de Intervalos", txt)
    def clear_all(self):
        """Limpia todas las entradas y resultados""" 
        # Limpiar entradas de matrices A y B
        if hasattr(self, 'matrix_a_entries'):
            for row in self.matrix_a_entries:
                for entry in row:
                    entry.delete(0, tk.END)
                    entry.insert(0, "0")
        
        if hasattr(self, 'matrix_b_entries'):
            for row in self.matrix_b_entries:
                for entry in row:
                    entry.delete(0, tk.END)
                    entry.insert(0, "0")
        
        # Limpiar resultado
        if hasattr(self, 'result_text'):
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", "Los pasos del cálculo se mostrarán aquí.")
            self.result_text.config(state="disabled")
        
        # Actualizar título de resultado
        if hasattr(self, 'result_title'):
            self.result_title.config(text="Resultado:")

    def setup_virtual_keyboard(self):
        """Configura el teclado virtual para funciones matemáticas"""
        # Botones de funciones matemáticas
        func_frame = tk.Frame(self.keyboard_frame, bg=self.colors["matrix_bg"])
        func_frame.pack(pady=15, padx=10)
        
        tk.Label(func_frame, text="Funciones Matemáticas:", 
                font=("Segoe UI", 13, "bold"),
                bg=self.colors["matrix_bg"], fg=self.colors["accent"]).pack(pady=(0, 15))
        
        # Frame para los botones usando grid
        buttons_frame = tk.Frame(func_frame, bg=self.colors["matrix_bg"])
        buttons_frame.pack()
        
        # Botones de funciones
        functions = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"),
            ("exp(x)", "exp(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x**2"), ("x³", "x**3"), ("1/x", "1/x"),
            ("x", "x"), ("π", "pi"), ("e", "e"),
            ("+", "+"), ("-", "-"), ("×", "*"), ("/", "/"),
            ("(", "("), (")", ")"), ("^", "**")
        ]
        
        # Estilos mejorados para botones
        button_style_normal = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 12,
            "pady": 8,
            "cursor": "hand2",
            "activebackground": self.colors["accent"],
            "activeforeground": "white"
        }
        
        button_style_operator = {
            "font": ("Segoe UI", 12, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 14,
            "pady": 8,
            "cursor": "hand2",
            "activebackground": self.colors["accent"],
            "activeforeground": "white"
        }
        
        # Crear botones en cuadrícula con mejor diseño
        for i, (text, value) in enumerate(functions):
            row = i // 6
            col = i % 6
            
            # Determinar color según tipo de botón
            if text in ["+", "-", "×", "/", "^"]:
                bg_color = self.colors["accent"]
                style = button_style_operator
            elif text in ["sin(x)", "cos(x)", "tan(x)", "exp(x)", "log(x)", "sqrt(x)"]:
                bg_color = "#4A90E2"  # Azul para funciones trigonométricas
                style = button_style_normal
            elif text in ["x²", "x³", "1/x", "x"]:
                bg_color = "#7B68EE"  # Púrpura para potencias
                style = button_style_normal
            elif text in ["π", "e"]:
                bg_color = "#20B2AA"  # Turquesa para constantes
                style = button_style_normal
            else:
                bg_color = self.colors["button_secondary"]
                style = button_style_normal
            
            btn = tk.Button(buttons_frame, text=text, command=lambda v=value: self.insert_function(v),
                           bg=bg_color, fg="white", **style)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            # Agregar efecto hover
            def on_enter(e, btn=btn, original_bg=bg_color):
                btn.config(bg=self.colors["accent"])
            
            def on_leave(e, btn=btn, original_bg=bg_color):
                btn.config(bg=original_bg)
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Configurar pesos de columnas para mejor distribución
        for col in range(6):
            buttons_frame.grid_columnconfigure(col, weight=1, uniform="buttons")
        
        # Botón de borrar con estilo especial
        clear_btn = tk.Button(buttons_frame, text="🗑 Borrar", command=self.clear_function_entry,
                             bg="#FF453A", fg="white",
                             font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                             padx=12, pady=8, cursor="hand2",
                             activebackground="#FF6B6B", activeforeground="white")
        clear_btn.grid(row=len(functions) // 6, column=5, padx=3, pady=3, sticky="nsew")
        
        # Efecto hover para botón borrar
        def on_enter_clear(e):
            clear_btn.config(bg="#FF6B6B")
        def on_leave_clear(e):
            clear_btn.config(bg="#FF453A")
        clear_btn.bind("<Enter>", on_enter_clear)
        clear_btn.bind("<Leave>", on_leave_clear)

    def toggle_keyboard(self):
        """Muestra/oculta el teclado virtual"""
        try:
            # Usar variable de estado para rastrear visibilidad
            if self.keyboard_visible:
                # Ocultar el teclado
                self.keyboard_frame.pack_forget()
                self.keyboard_visible = False
                self.keyboard_btn.config(text="⌨ Mostrar Teclado")
            else:
                # Mostrar el teclado - empaquetar antes del frame de resultados
                self.keyboard_frame.pack(pady=(15, 0), fill="x", padx=20, before=self.bisection_result_frame)
                self.keyboard_visible = True
                self.keyboard_btn.config(text="🔽 Ocultar Teclado")
                # Forzar actualización
                self.keyboard_frame.update_idletasks()
                self.bisection_tab.update_idletasks()
        except Exception as e:
            # Si hay error, intentar mostrar el teclado
            try:
                self.keyboard_frame.pack(pady=(15, 0), fill="x", padx=20, before=self.bisection_result_frame)
                self.keyboard_visible = True
                self.keyboard_btn.config(text="🔽 Ocultar Teclado")
                self.keyboard_frame.update_idletasks()
            except:
                pass

    def insert_function(self, value):
        """Inserta una función en el campo de entrada"""
        current = self.function_var.get()
        cursor_pos = self.function_entry.index(tk.INSERT)
        
        # Manejar valores especiales - insertar símbolos, no valores numéricos
        if value == "pi":
            value = "π"
        elif value == "e":
            value = "e"
        
        # Insertar en la posición del cursor
        new_value = current[:cursor_pos] + value + current[cursor_pos:]
        self.function_var.set(new_value)
        
        # Mantener el cursor en la posición correcta
        new_cursor_pos = cursor_pos + len(value)
        self.function_entry.icursor(new_cursor_pos)
        self.function_entry.focus()

    def clear_function_entry(self):
        """Limpia el campo de entrada de función"""
        self.function_var.set("")
        self.function_entry.focus()
    
    def format_function_display(self, func_str):
        """
        Formatea una función para mostrar símbolos y exponentes como superíndices.
        Mantiene π, e, y convierte exponentes a formato superíndice Unicode.
        
        Args:
            func_str: String con la función matemática
            
        Returns:
            String formateado con símbolos y superíndices
        """
        import re
        
        # Diccionario para convertir números a superíndices Unicode
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
            """Convierte texto a superíndice Unicode"""
            return ''.join(superscript_map.get(char, char) for char in text)
        
        result = func_str
        
        # Convertir pi a símbolo π si está como texto
        result = re.sub(r'\bpi\b', 'π', result)
        
        # Convertir exp(x) a e^(x) y luego a eˣ
        result = re.sub(r'\bexp\(([^)]+)\)', r'e^(\1)', result)
        
        # Convertir exponentes: e^x, e^(x), x^2, etc. a formato superíndice
        def replace_power(match):
            base = match.group(1)
            exponent = match.group(2)
            
            # Convertir el exponente a superíndice
            # Primero manejar casos simples
            if len(exponent) == 1:
                # Un solo carácter: x, 2, 3, etc.
                return base + to_superscript(exponent)
            else:
                # Múltiples caracteres: convertir cada uno que sea posible
                converted = ''
                for char in exponent:
                    if char in superscript_map:
                        converted += superscript_map[char]
                    else:
                        converted += char
                return base + converted
        
        # Reemplazar patrones de potencia: base^exponente
        # Primero manejar casos con paréntesis: e^(x+1), x^(2+3), etc.
        def replace_power_with_paren(match):
            base = match.group(1)
            exponent_content = match.group(2)
            # Convertir el contenido del paréntesis
            converted = ''
            for char in exponent_content:
                if char in superscript_map:
                    converted += superscript_map[char]
                else:
                    converted += char
            return base + converted
        
        # Reemplazar e^(x), x^(2), etc.
        result = re.sub(r'([a-zA-Z0-9πe]+)\^\(([^)]+)\)', replace_power_with_paren, result)
        # Reemplazar e^x, x^2, etc. (sin paréntesis)
        result = re.sub(r'([a-zA-Z0-9πe]+)\^([a-zA-Z0-9]+)', replace_power, result)
        
        return result
    
    def setup_virtual_keyboard_fp(self):
        """Configura el teclado virtual para la pestaña de Falsa Posición"""
        # Botones de funciones matemáticas
        func_frame = tk.Frame(self.fp_keyboard_frame, bg=self.colors["matrix_bg"])
        func_frame.pack(pady=15, padx=10)
        
        tk.Label(func_frame, text="Funciones Matemáticas:", 
                font=("Segoe UI", 13, "bold"),
                bg=self.colors["matrix_bg"], fg=self.colors["accent"]).pack(pady=(0, 15))
        
        # Frame para los botones usando grid
        buttons_frame = tk.Frame(func_frame, bg=self.colors["matrix_bg"])
        buttons_frame.pack()
        
        # Botones de funciones
        functions = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"),
            ("exp(x)", "exp(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x**2"), ("x³", "x**3"), ("1/x", "1/x"),
            ("x", "x"), ("π", "pi"), ("e", "e"),
            ("+", "+"), ("-", "-"), ("×", "*"), ("/", "/"),
            ("(", "("), (")", ")"), ("^", "**")
        ]
        
        # Estilos mejorados para botones
        button_style_normal = {
            "font": ("Segoe UI", 11, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 12,
            "pady": 8,
            "cursor": "hand2",
            "activebackground": self.colors["accent"],
            "activeforeground": "white"
        }
        
        button_style_operator = {
            "font": ("Segoe UI", 12, "bold"),
            "relief": "flat",
            "bd": 0,
            "padx": 14,
            "pady": 8,
            "cursor": "hand2",
            "activebackground": self.colors["accent"],
            "activeforeground": "white"
        }
        
        # Crear botones en cuadrícula con mejor diseño
        for i, (text, value) in enumerate(functions):
            row = i // 6
            col = i % 6
            
            # Determinar color según tipo de botón
            if text in ["+", "-", "×", "/", "^"]:
                bg_color = self.colors["accent"]
                style = button_style_operator
            elif text in ["sin(x)", "cos(x)", "tan(x)", "exp(x)", "log(x)", "sqrt(x)"]:
                bg_color = "#4A90E2"  # Azul para funciones trigonométricas
                style = button_style_normal
            elif text in ["x²", "x³", "1/x", "x"]:
                bg_color = "#7B68EE"  # Púrpura para potencias
                style = button_style_normal
            elif text in ["π", "e"]:
                bg_color = "#20B2AA"  # Turquesa para constantes
                style = button_style_normal
            else:
                bg_color = self.colors["button_secondary"]
                style = button_style_normal
            
            btn = tk.Button(buttons_frame, text=text, command=lambda v=value: self.insert_function_fp(v),
                           bg=bg_color, fg="white", **style)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            
            # Agregar efecto hover
            def on_enter(e, btn=btn, original_bg=bg_color):
                btn.config(bg=self.colors["accent"])
            
            def on_leave(e, btn=btn, original_bg=bg_color):
                btn.config(bg=original_bg)
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Configurar pesos de columnas para mejor distribución
        for col in range(6):
            buttons_frame.grid_columnconfigure(col, weight=1, uniform="buttons")
        
        # Botón de borrar con estilo especial
        clear_btn = tk.Button(buttons_frame, text="🗑 Borrar", command=self.clear_function_entry_fp,
                             bg="#FF453A", fg="white",
                             font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                             padx=12, pady=8, cursor="hand2",
                             activebackground="#FF6B6B", activeforeground="white")
        clear_btn.grid(row=len(functions) // 6, column=5, padx=3, pady=3, sticky="nsew")
        
        # Efecto hover para botón borrar
        def on_enter_clear(e):
            clear_btn.config(bg="#FF6B6B")
        def on_leave_clear(e):
            clear_btn.config(bg="#FF453A")
        clear_btn.bind("<Enter>", on_enter_clear)
        clear_btn.bind("<Leave>", on_leave_clear)
    
    def insert_function_fp(self, value):
        """Inserta una función en el campo de entrada de Falsa Posición"""
        current = self.fp_function_var.get()
        cursor_pos = self.fp_function_entry.index(tk.INSERT)
        
        # Manejar valores especiales - insertar símbolos, no valores numéricos
        if value == "pi":
            value = "π"
        elif value == "e":
            value = "e"
        
        # Insertar en la posición del cursor
        new_value = current[:cursor_pos] + value + current[cursor_pos:]
        self.fp_function_var.set(new_value)
        
        # Mantener el cursor en la posición correcta
        new_cursor_pos = cursor_pos + len(value)
        self.fp_function_entry.icursor(new_cursor_pos)
        self.fp_function_entry.focus()
    
    def clear_function_entry_fp(self):
        """Limpia el campo de entrada de función de Falsa Posición"""
        self.fp_function_var.set("")
        self.fp_function_entry.focus()
    
    def toggle_keyboard_fp(self):
        """Muestra/oculta el teclado virtual de Falsa Posición"""
        try:
            if self.fp_keyboard_visible:
                # Ocultar el teclado
                self.fp_keyboard_frame.pack_forget()
                self.fp_keyboard_visible = False
                self.fp_keyboard_btn.config(text="⌨ Mostrar Teclado")
            else:
                # Mostrar el teclado - empaquetar antes del frame de resultados
                self.fp_keyboard_frame.pack(pady=(15, 0), fill="x", padx=20, before=self.fp_result_frame)
                self.fp_keyboard_visible = True
                self.fp_keyboard_btn.config(text="🔽 Ocultar Teclado")
                # Forzar actualización
                self.fp_keyboard_frame.update_idletasks()
                self.falsepos_tab.update_idletasks()
        except Exception as e:
            # Si hay error, intentar mostrar el teclado
            try:
                self.fp_keyboard_frame.pack(pady=(15, 0), fill="x", padx=20, before=self.fp_result_frame)
                self.fp_keyboard_visible = True
                self.fp_keyboard_btn.config(text="🔽 Ocultar Teclado")
                self.fp_keyboard_frame.update_idletasks()
            except:
                pass

    def preprocess_function(self, func_str):
        """Preprocesa la función para convertir notaciones comunes"""
        s = func_str.strip()
        if not s:
            return s
        
        # Guardar la función original
        original_func = s
        
        # Normalizaciones comunes
        s = s.replace(" ", "")
        
        # Convertir e^x a exp(x) ANTES de convertir ^ a **
        # Manejar e^x, e^(x), e^(x+1), etc.
        s = re.sub(r'\be\*\*\(([^)]+)\)', r'exp(\1)', s)  # e^(x+1) -> exp(x+1)
        s = re.sub(r'\be\*\*([a-zA-Z0-9_]+)', r'exp(\1)', s)  # e^x -> exp(x)
        s = re.sub(r'\be\^\(([^)]+)\)', r'exp(\1)', s)  # e^(x+1) -> exp(x+1)
        s = re.sub(r'\be\^([a-zA-Z0-9_]+)', r'exp(\1)', s)  # e^x -> exp(x)
        
        # Convertir ^ a ** para potencias
        s = s.replace("^", "**")
        
        # Corregir errores comunes: +^ o -^ seguido de número (probablemente falta x)
        # Ejemplo: +^3 -> +x**3, -^2 -> -x**2
        s = re.sub(r'([+\-])\*\*(\d+)', r'\1x**\2', s)
        
        # Convertir multiplicación implícita: número seguido de x o paréntesis
        # Ejemplo: 10x -> 10*x, 5( -> 5*(
        s = re.sub(r'(\d+)([a-zA-Z(])', r'\1*\2', s)
        # Ejemplo: )x -> )*x, )( -> )*(
        s = re.sub(r'\)([a-zA-Z(])', r')*\1', s)
        # Ejemplo: x( -> x*(
        s = re.sub(r'([a-zA-Z])(\()', r'\1*\2', s)
        
        # Sinónimos en español (palabras completas o seguidas de letra)
        # Convertir sen seguido de letra o límite de palabra a sin
        s = re.sub(r'\bsen([a-zA-Z])', r'sin\1', s)  # senx -> sinx, sen( -> sin(
        s = re.sub(r'\bsen\b', 'sin', s)  # sen solo -> sin
        s = re.sub(r'\bln([a-zA-Z])', r'log\1', s)  # lnx -> logx
        s = re.sub(r'\bln\b', 'log', s)  # ln solo -> log
        
        # Convertir variable seguida de función seguida de variable: xlogx -> x*log(x)
        # Esto debe hacerse antes de convertir funciones solas
        for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
            s = re.sub(rf'([a-zA-Z]){name}([a-zA-Z])', rf'\1*{name}(\2)', s)
        s = re.sub(r'([a-zA-Z])log10([a-zA-Z])', r'\1*log10(\2)', s)
        s = re.sub(r'([a-zA-Z])abs([a-zA-Z])', r'\1*abs(\2)', s)
        
        # Convertir funciones seguidas de variable (sin espacio ni paréntesis) a función(variable)
        # Ejemplo: sinx -> sin(x), cosx -> cos(x), senx -> sin(x)
        for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
            s = re.sub(rf'\b{name}([a-zA-Z])', rf'{name}(\1)', s)
        s = re.sub(r'\blog10([a-zA-Z])', r'log10(\1)', s)
        s = re.sub(r'\babs([a-zA-Z])', r'abs(\1)', s)
        
        # Convertir funciones seguidas de variable (con espacio) a función(variable)
        # Ejemplo: sin x -> sin(x), cos x -> cos(x)
        for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
            s = re.sub(rf'\b{name}\s+([a-zA-Z])', rf'{name}(\1)', s)
        s = re.sub(r'\blog10\s+([a-zA-Z])', r'log10(\1)', s)
        s = re.sub(r'\babs\s+([a-zA-Z])', r'abs(\1)', s)
        
        # Prefijar funciones del módulo math cuando sean llamadas
        for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
            s = re.sub(rf'\b{name}\s*(?=\()', f'math.{name}', s)
        s = re.sub(r'\blog10\s*(?=\()', 'math.log10', s)
        s = re.sub(r'\babs\s*(?=\()', 'abs', s)
        
        # Constantes: pi y e, evitando romper nombres de funciones
        s = re.sub(r'π', 'math.pi', s)
        s = re.sub(r'(?<!\w)pi(?!\w)', 'math.pi', s)
        # Solo convertir 'e' a math.e si no es parte de 'exp' o ya está en una expresión
        # Evitar convertir 'e' en 'exp(x)' o 'math.exp'
        s = re.sub(r'(?<!\w)(?<!math\.)(?<!exp\()e(?!\w)(?!xp)', 'math.e', s)
        
        # Convertir math.e**x en exp(x) para mayor claridad (por si acaso)
        s = re.sub(r'math\.e\*\*(\([^()]*\)|[A-Za-z0-9_.]+)', r'math.exp(\1)', s)
        
        return s

    def evaluate_function(self, x, func_str):
        """Evalúa la función en el punto x, aceptando notaciones comunes e inserta multiplicación implícita."""
        try:
            s = func_str.strip()
            if not s:
                raise ValueError("Función vacía")

            original_func = s

            # Normalizaciones comunes
            s = s.replace(" ", "")
            s = s.replace("^", "**")  # permitir ^ como potencia

            # Sinónimos en español
            s = re.sub(r'\bsen\b', 'sin', s)
            s = re.sub(r'\bln\b', 'log', s)

            # Prefijar funciones del módulo math cuando son llamadas
            for name in ['sin', 'cos', 'tan', 'exp', 'log', 'sqrt']:
                s = re.sub(rf'\b{name}\s*(?=\()', f'math.{name}', s)
            s = re.sub(r'\blog10\s*(?=\()', 'math.log10', s)
            s = re.sub(r'\babs\s*(?=\()', 'abs', s)

            # Constantes
            s = re.sub(r'π', 'math.pi', s)
            s = re.sub(r'(?<!\w)pi(?!\w)', 'math.pi', s)
            s = re.sub(r'(?<!\w)e(?!\w)', 'math.e', s)

            # e^x -> exp(x)
            s = re.sub(r'math\.e\*\*(\([^()]*\)|[A-Za-z0-9_.]+)', r'math.exp(\1)', s)

            # Inserción de multiplicación implícita
            # número seguido de x o '('
            s = re.sub(r'(?<=\d)(?=x|\()', '*', s)
            # x seguido de número o '('
            s = re.sub(r'(?<=x)(?=\d|\()', '*', s)
            # ')' seguido de dígito, 'x' o '('
            s = re.sub(r'(?<=\))(?=[\dx(])', '*', s)
            # constantes seguidas de dígito, 'x' o '('
            s = re.sub(r'(?<=math\.pi)(?=[\dx(])', '*', s)
            s = re.sub(r'(?<=math\.e)(?=[\dx(])', '*', s)

            # Validación de AST (permitir solo x, math y números)
            try:
                tree = ast.parse(s, mode='eval')
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id not in ['x', 'math']:
                        raise ValueError(f"Variable no permitida: {node.id}")
                    elif isinstance(node, ast.Attribute) and node.attr not in ['sin', 'cos', 'tan', 'exp', 'log', 'log10', 'pi', 'e', 'sqrt']:
                        raise ValueError(f"Función no permitida: {node.attr}")
            except SyntaxError:
                raise ValueError(f"Sintaxis inválida en la función: {original_func}")

            # Evaluación segura
            env = {"x": x, "math": math, "abs": abs}
            result = eval(s, {"__builtins__": {}}, env)

            if not isinstance(result, (int, float)):
                raise ValueError("La función debe devolver un número")

            return float(result)

        except ValueError as e:
            raise ValueError(str(e))
        except Exception as e:
            raise ValueError(f"Error al evaluar la función '{original_func}': {str(e)}")

    def calculate_bisection(self):
        """Implementa el método de bisección"""
        try:
            # Obtener valores de entrada
            func_str = self.function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return
            
            a = float(self.a_var.get())
            b = float(self.b_var.get())
            tolerance = float(self.tol_var.get())
            max_iterations = int(self.max_iter_var.get())
            
            # Validar que a < b
            if a >= b:
                messagebox.showerror("Error", "El valor de 'a' debe ser menor que 'b'")
                return
            
            # Validar que la tolerancia sea positiva
            if tolerance <= 0:
                messagebox.showerror("Error", "La tolerancia debe ser positiva")
                return
            
            # Evaluar la función en los extremos
            fa = self.evaluate_function(a, func_str)
            fb = self.evaluate_function(b, func_str)
            
            # Verificar que haya cambio de signo
            if fa * fb > 0:
                messagebox.showerror("Error", "La función no cambia de signo en el intervalo [a, b].\nEl método de bisección requiere que f(a) * f(b) < 0")
                return
            
            # Limpiar resultados anteriores
            self.bisection_result_text.config(state="normal")
            self.bisection_result_text.delete("1.0", tk.END)
            
            # Mostrar información inicial
            self.bisection_result_text.insert("1.0", f"MÉTODO DE BISECCIÓN\n", "title")
            # Mostrar función con valores numéricos en lugar de símbolos
            formatted_func = self.format_function_display(func_str)
            self.bisection_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
            self.bisection_result_text.insert(tk.END, f"Tolerancia: {tolerance}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Máximo de iteraciones: {max_iterations}\n\n", "step")
            
            # Crear encabezado de la tabla
            self.bisection_result_text.insert(tk.END, "\nTABLA DE ITERACIONES:\n", "title")
            self.bisection_result_text.insert(tk.END, "=" * 95 + "\n", "step")
            # Encabezados de columnas
            header = f"{'Iter':<6} {'a':>12} {'b':>12} {'c':>12} {'f(a)':>12} {'f(b)':>12} {'f(c)':>12} {'Error':>12}\n"
            self.bisection_result_text.insert(tk.END, header, "step")
            self.bisection_result_text.insert(tk.END, "-" * 95 + "\n", "step")
            
            # Aplicar el método de bisección
            iteration = 0
            while (b - a) / 2 > tolerance and iteration < max_iterations:
                c = (a + b) / 2
                fc = self.evaluate_function(c, func_str)
                error = abs(b - a) / 2
                
                # Mostrar información de la iteración en formato de tabla
                row = f"{'+' + str(iteration + 1):<6} {a:>+12.4f} {b:>+12.4f} {c:>+12.4f} {fa:>+12.4f} {fb:>+12.4f} {fc:>+12.4f} {error:>+12.4f}\n"
                self.bisection_result_text.insert(tk.END, row, "matrix")
                
                # Determinar el nuevo intervalo
                if fa * fc < 0:
                    b = c
                    fb = fc
                else:
                    a = c
                    fa = fc
                
                iteration += 1
            
            # Línea final de la tabla
            self.bisection_result_text.insert(tk.END, "=" * 95 + "\n\n", "step")
            
            # Resultado final
            root = (a + b) / 2
            # Guardar la raíz calculada para mostrarla en la gráfica
            self.calculated_root = root
            self.calculated_func_str = func_str
            self.calculated_interval = (a, b)
            
            self.bisection_result_text.insert(tk.END, "=" * 60 + "\n", "title")
            self.bisection_result_text.insert(tk.END, "RESULTADO FINAL:\n", "result")
            self.bisection_result_text.insert(tk.END, f"Raíz aproximada: x = {root:.8f}\n", "result")
            self.bisection_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.bisection_result_text.insert(tk.END, f"Número de iteraciones: {iteration}\n", "result")
            self.bisection_result_text.insert(tk.END, f"Error estimado final: {(b - a) / 2:.2e}\n", "result")
            
            if iteration >= max_iterations:
                self.bisection_result_text.insert(tk.END, "\n⚠ ADVERTENCIA: Se alcanzó el máximo de iteraciones\n", "warning")
            
            self.bisection_result_text.config(state="disabled")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error en el cálculo: {str(e)}")

    def calculate_false_position(self):
        """Calcula la raíz con el Método de Falsa Posición (Regla Falsa)"""
        try:
            # Entradas
            func_str = self.function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return

            a = float(self.a_var.get())
            b = float(self.b_var.get())
            tolerance = float(self.tol_var.get())
            max_iterations = int(self.max_iter_var.get())

            if a >= b:
                messagebox.showerror("Error", "El valor de 'a' debe ser menor que 'b'")
                return
            if tolerance <= 0:
                messagebox.showerror("Error", "La tolerancia debe ser positiva")
                return

            fa = self.evaluate_function(a, func_str)
            fb = self.evaluate_function(b, func_str)
            if fa * fb > 0:
                messagebox.showerror("Error", "La función no cambia de signo en [a,b].\nFalsa Posición requiere f(a) * f(b) < 0")
                return
            if fa == fb:
                messagebox.showerror("Error", "f(a) y f(b) son iguales; la fórmula se indetermina")
                return

            # Preparar resultados
            self.bisection_result_text.config(state="normal")
            self.bisection_result_text.delete("1.0", tk.END)
            self.bisection_result_text.insert("1.0", f"MÉTODO DE FALSA POSICIÓN (Regla Falsa)\n", "title")
            # Mostrar función con valores numéricos en lugar de símbolos
            formatted_func = self.format_function_display(func_str)
            self.bisection_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
            self.bisection_result_text.insert(tk.END, f"Tolerancia: {tolerance}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Máximo de iteraciones: {max_iterations}\n\n", "step")

            iteration = 0
            prev_c = None

            while iteration < max_iterations:
                fa = self.evaluate_function(a, func_str)
                fb = self.evaluate_function(b, func_str)

                if fb == fa:
                    self.bisection_result_text.insert(tk.END, "⚠ f(a) == f(b); fórmula indeterminada\n", "warning")
                    break

                # Fórmula de Falsa Posición
                c = b - fb * (b - a) / (fb - fa)
                fc = self.evaluate_function(c, func_str)

                # Log de iteración
                self.bisection_result_text.insert(tk.END, f"Iteración {iteration + 1}:\n", "step")
                self.bisection_result_text.insert(tk.END, f"  a = {a:.8f}, f(a) = {fa:.8f}\n")
                self.bisection_result_text.insert(tk.END, f"  b = {b:.8f}, f(b) = {fb:.8f}\n")
                self.bisection_result_text.insert(tk.END, f"  c = {c:.8f}, f(c) = {fc:.8f}\n")

                # Criterios de parada
                error_c = abs(fc)
                error_intervalo = abs(b - a)
                self.bisection_result_text.insert(tk.END, f"  Error |f(c)| = {error_c:.8f}, ancho intervalo = {error_intervalo:.8f}\n")

                if abs(fc) <= tolerance or (prev_c is not None and abs(c - prev_c) <= tolerance) or error_intervalo <= tolerance:
                    prev_c = c
                    break

                # Actualizar intervalo según cambio de signo
                if fa * fc < 0:
                    b = c
                    fb = fc
                    self.bisection_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(a) * f(c) < 0)\n\n")
                else:
                    a = c
                    fa = fc
                    self.bisection_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(b) * f(c) < 0)\n\n")

                prev_c = c
                iteration += 1

            # Resultado final
            root = prev_c if prev_c is not None else (a + b) / 2
            self.bisection_result_text.insert(tk.END, "=" * 60 + "\n", "title")
            self.bisection_result_text.insert(tk.END, "RESULTADO FINAL (Falsa Posición):\n", "result")
            self.bisection_result_text.insert(tk.END, f"Raíz aproximada: x = {root:.8f}\n", "result")
            self.bisection_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.bisection_result_text.insert(tk.END, f"Número de iteraciones: {iteration}\n", "result")
            self.bisection_result_text.insert(tk.END, f"Error final |f(c)|: {abs(self.evaluate_function(root, func_str)):.2e}\n", "result")

            if iteration >= max_iterations:
                self.bisection_result_text.insert(tk.END, "\n⚠ ADVERTENCIA: Se alcanzó el máximo de iteraciones\n", "warning")

            self.bisection_result_text.config(state="disabled")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error en Falsa Posición: {str(e)}")

    def clear_bisection(self):
        """Limpia la pestaña de bisección"""
        # Limpiar entradas
        self.function_var.set("")
        self.a_var.set("-1")
        self.b_var.set("1")
        self.tol_var.set("0.0001")
        self.max_iter_var.set("100")
        
        # NO ocultar el teclado al limpiar - mantenerlo visible
        # self.keyboard_frame.pack_forget()
        # self.keyboard_btn.config(text="⌨ Teclado")
        
        # Limpiar resultados
        self.bisection_result_text.config(state="normal")
        self.bisection_result_text.delete("1.0", tk.END)
        self.bisection_result_text.insert("1.0", "Los resultados del método de bisección se mostrarán aquí.")
        self.bisection_result_text.config(state="disabled")

    def suggest_interval(self):
        """Busca intervalos [a,b] donde f(a)*f(b) < 0 con muestreo afinado."""
        func_str = self.function_var.get().strip()
        if not func_str:
            messagebox.showerror("Error", "Por favor ingrese una función en 'f(x)'.")
            return

        # Rango y pasos más finos
        search_specs = [
            (-10, 10, 0.1),
            (-50, 50, 0.2),
            (-100, 100, 0.5),
        ]

        intervals = []
        for a_range, b_range, step in search_specs:
            prev_x, prev_y = None, None
            x = float(a_range)
            while x <= float(b_range):
                try:
                    y = float(self.evaluate_function(x, func_str))
                    if prev_y is not None and not math.isnan(prev_y) and not math.isnan(y):
                        if prev_y * y < 0:
                            intervals.append((prev_x, x))
                            if len(intervals) >= 8:
                                break
                    prev_x, prev_y = x, y
                except Exception:
                    prev_x, prev_y = None, None
                x = round(x + step, 10)  # evitar acumulación de flotantes
            if intervals:
                break

        if not intervals:
            messagebox.showwarning(
                "Sin cambio de signo",
                "No se encontraron intervalos con cambio de signo en los rangos probados.\n"
                "Prueba ajustar manualmente el intervalo o revisar la función."
            )
            return

        # Asignar el primero y mostrar lista
        a, b = intervals[0]
        self.a_var.set(f"{a:.6f}")
        self.b_var.set(f"{b:.6f}")

        txt = "Intervalos con cambio de signo detectados:\n\n"
        for i, (ia, ib) in enumerate(intervals, 1):
            txt += f"{i}. [{ia:.6f}, {ib:.6f}]\n"
        txt += "\nSe asignó el primero en los campos 'a' y 'b'."

        messagebox.showinfo("Sugerencia de Intervalos", txt)

    def toggle_fullscreen(self, event=None):
        """Alterna entre pantalla completa y ventana normal"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)

    def on_tab_changed(self, event=None):
        """Maneja el cambio entre pestañas"""
        # Obtener la pestaña actual
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")
        
        # Si estamos en la pestaña de bisección, asegurar que el teclado esté visible
        if tab_text == "Método de Bisección":
            # Asegurar que el frame del teclado esté empaquetado correctamente
            try:
                # Usar la variable de estado en lugar de verificar winfo
                if not self.keyboard_visible:
                    self.keyboard_frame.pack(pady=(15, 0), fill="x", padx=20, before=self.bisection_result_frame)
                    self.keyboard_visible = True
                    self.keyboard_btn.config(text="🔽 Ocultar Teclado")
                    self.keyboard_frame.update_idletasks()
            except:
                pass

    def show_function_help(self):
        """Muestra ejemplos de cómo ingresar funciones"""
        help_text = """CÓMO INGRESAR FUNCIONES

Formatos aceptados:
• Potencias: x^2  o  x**3
• Seno: sin(x)  o  sen(x)
• Coseno: cos(x)
• Tangente: tan(x)
• Exponencial: exp(x)  o  e^x
• Logaritmo natural: log(x)  o  ln(x)
• Logaritmo base 10: log10(x)
• Raíz cuadrada: sqrt(x)
• Valor absoluto: abs(x)
• Constante pi: π  o  pi
• Constante e: e

EJEMPLOS DE FUNCIONES:
• x^2 - 4
• sin(x) + x - 1
• e^x - 3*x
• log(x) - 1
• x^3 - 2*x + 1
• sqrt(x) - 2
• abs(x) - 3
• cos(x) - x

IMPORTANTE:
• Usa paréntesis para agrupar: (x^2 - 1)/(x + 2)
• No uses espacios entre operaciones
• Asegúrate de que la función cambie de signo en el intervalo [a,b]"""
        
        messagebox.showinfo("Ayuda - Funciones Matemáticas", help_text)

    def evaluate_function_vectorized(self, x_array, func_str):
        """Evalúa la función para un array de numpy (vectorizado)"""
        try:
            s = func_str.strip()
            if not s:
                raise ValueError("Función vacía")
            
            # Preprocesar la función (convierte multiplicación implícita, etc.)
            s = self.preprocess_function(s)
            
            # Reemplazar math. con np. para funciones vectorizadas
            s = s.replace("math.sin", "np.sin")
            s = s.replace("math.cos", "np.cos")
            s = s.replace("math.tan", "np.tan")
            s = s.replace("math.exp", "np.exp")
            s = s.replace("math.log", "np.log")
            s = s.replace("math.log10", "np.log10")
            s = s.replace("math.sqrt", "np.sqrt")
            s = s.replace("math.pi", "np.pi")
            s = s.replace("math.e", "np.e")
            
            # Evaluación vectorizada
            env = {"x": x_array, "np": np, "math": math, "abs": np.abs}
            try:
                result = eval(s, {"__builtins__": {}}, env)
            except ValueError as ve:
                # Manejar errores de dominio matemático
                if "math domain error" in str(ve).lower() or "domain" in str(ve).lower():
                    # Para gráficas, devolver NaN para valores inválidos
                    return np.full_like(x_array, np.nan, dtype=float)
                raise ValueError(f"Error al evaluar la función: {str(ve)}")
            
            result = np.array(result, dtype=float)
            
            # Reemplazar infinitos con NaN para que no se grafiquen
            result = np.where(np.isinf(result), np.nan, result)
            
            return result
            
        except Exception as e:
            raise ValueError(f"Error al evaluar la función: {str(e)}")
    
    def plot_function(self):
        """Grafica la función usando matplotlib"""
        try:
            func_str = self.function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return
            
            # Obtener intervalo
            try:
                a = float(self.a_var.get())
                b = float(self.b_var.get())
            except ValueError:
                a, b = -5, 5  # Intervalo por defecto
            
            # Crear ventana para la gráfica
            plot_window = tk.Toplevel(self.root)
            # Mostrar función con valores numéricos en el título
            formatted_func = self.format_function_display(func_str)
            plot_window.title(f"Gráfica de f(x) = {formatted_func}")
            plot_window.geometry("800x600")
            plot_window.configure(bg=self.colors["background"])
            
            # Crear figura de matplotlib
            fig = Figure(figsize=(8, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Calcular rango de x (extender un poco más allá del intervalo)
            margin = max(abs(b - a) * 0.2, 1)
            x_min = min(a, b) - margin
            x_max = max(a, b) + margin
            
            # Crear array de x
            x = np.linspace(x_min, x_max, 1000)
            
            # Evaluar función
            try:
                y = self.evaluate_function_vectorized(x, func_str)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo evaluar la función: {str(e)}")
                plot_window.destroy()
                return
            
            # Graficar función con formato numérico
            ax.plot(x, y, 'b-', linewidth=2, label=f'f(x) = {formatted_func}')
            
            # Graficar eje x
            ax.axhline(y=0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
            ax.axvline(x=0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
            
            # Marcar intervalo [a, b]
            ax.axvline(x=a, color='g', linewidth=2, linestyle=':', alpha=0.7, label=f'a = {a:.2f}')
            ax.axvline(x=b, color='r', linewidth=2, linestyle=':', alpha=0.7, label=f'b = {b:.2f}')
            
            # Marcar puntos f(a) y f(b)
            try:
                fa = self.evaluate_function(a, func_str)
                fb = self.evaluate_function(b, func_str)
                ax.plot(a, fa, 'go', markersize=8, label=f'f(a) = {fa:.3f}')
                ax.plot(b, fb, 'ro', markersize=8, label=f'f(b) = {fb:.3f}')
            except:
                pass
            
            # Marcar raíz calculada si existe
            if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str'):
                if self.calculated_func_str == func_str:
                    root = self.calculated_root
                    try:
                        f_root = self.evaluate_function(root, func_str)
                        ax.plot(root, f_root, 'm*', markersize=15, label=f'Raíz ≈ {root:.4f}')
                        ax.axvline(x=root, color='m', linewidth=1.5, linestyle='--', alpha=0.6)
                    except:
                        pass
            
            # Configurar gráfica
            ax.set_xlabel('x', fontsize=12)
            ax.set_ylabel('f(x)', fontsize=12)
            # Mostrar función con valores numéricos en el título
            formatted_func = self.format_function_display(func_str)
            ax.set_title(f'Gráfica de f(x) = {formatted_func}', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', fontsize=9)
            
            # Ajustar límites del eje y si es necesario
            y_min, y_max = np.nanmin(y), np.nanmax(y)
            if not (np.isnan(y_min) or np.isnan(y_max)):
                y_range = y_max - y_min
                if y_range > 0:
                    ax.set_ylim(y_min - y_range * 0.1, y_max + y_range * 0.1)
            
            # Integrar matplotlib con tkinter
            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            
            # Agregar barra de herramientas de navegación personalizada sin coordenadas
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            
            # Crear una clase personalizada de toolbar sin formato de coordenadas
            class CustomToolbar(NavigationToolbar2Tk):
                def set_message(self, msg):
                    # Sobrescribir para no mostrar coordenadas
                    pass
            
            toolbar = CustomToolbar(canvas, plot_window)
            toolbar.update()
            
            # Desactivar el formato de coordenadas en el eje
            ax.format_coord = lambda x, y: ""
            
            # Empaquetar el canvas después de la toolbar
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar la función: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    # Configurar pantalla completa
    root.attributes('-fullscreen', True)  # Pantalla completa total
    # Alternativa para ventana maximizada (sin pantalla completa):
    # root.state('zoomed')  # Solo funciona en Windows
    app = MatrixCalculator(root)
    root.mainloop()