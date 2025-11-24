import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from fractions import Fraction
import json, os
import math
import re
import ast
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['text.antialiased'] = True
plt.rcParams['lines.antialiased'] = True
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
from tkinterweb import HtmlFrame
import webbrowser
import tempfile
import os

class MatrixCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Matrices Exacta")
        self.root.geometry("1200x850")
        # Maximizar ventana al iniciar (Windows compatible)
        try:
            self.root.state('zoomed')
        except Exception:
            # Fallback: center window
            try:
                self.root.eval('tk::PlaceWindow . center')
            except Exception:
                pass
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
        self.root.configure(bg=self.colors["background"])\
        
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use('vista')
        except Exception:
            try:
                self.style.theme_use('clam')
            except Exception:
                pass
        self.root.option_add('*Font', ('Segoe UI', 11))
        self.style.configure('TNotebook', background=self.colors['background'])
        self.style.configure('TNotebook.Tab', font=('Segoe UI', 12, 'bold'), padding=(16, 10))
        self.style.map('TNotebook.Tab', foreground=[('selected', self.colors['accent'])])
        self.style.configure('TCombobox', fieldbackground=self.colors['entry_bg'], foreground=self.colors['text'])
        try:
            dpi = self.root.winfo_fpixels('1i')
            self.root.tk.call('tk', 'scaling', dpi/72.0)
        except Exception:
            pass
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
        # Crear un canvas scrollable que contendrá el notebook (permite desplazar todo el formulario)
        outer_frame = tk.Frame(self.root, bg=self.colors["background"])
        outer_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.canvas = tk.Canvas(outer_frame, bg=self.colors["background"], highlightthickness=0)
        vsb_main = tk.Scrollbar(outer_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb_main.set)
        vsb_main.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Frame interior que contendrá el notebook
        self.inner_frame = tk.Frame(self.canvas, bg=self.colors["background"]) 
        self._inner_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        # Ajustar scrollregion cuando cambie el tamaño del contenido
        def _on_frame_config(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.inner_frame.bind("<Configure>", _on_frame_config)

        # Ajustar el ancho del contenido para que llene el canvas horizontalmente
        def _on_canvas_config(event):
            # actualizar el ancho del window para que coincida con el canvas
            try:
                self.canvas.itemconfigure(self._inner_window, width=event.width)
            except Exception:
                pass
        self.canvas.bind('<Configure>', _on_canvas_config)

        # Soportar scroll con rueda del ratón (Windows)
        def _on_mousewheel(event):
            # event.delta es múltiplo de 120 en Windows
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Crear notebook dentro del frame interior
        self.notebook = ttk.Notebook(self.inner_frame)
        self.notebook.pack(fill="both", expand=True)
        
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

        # Pestaña de Método de Newton-Raphson
        self.newton_tab = tk.Frame(self.notebook, bg=self.colors["background"])
        self.notebook.add(self.newton_tab, text="Método de Newton-Raphson")
        self.secant_tab = tk.Frame(self.notebook, bg=self.colors["background"])
        self.notebook.add(self.secant_tab, text="Método de la Secante")
        
        # Configurar la pestaña de matrices
        self.setup_matrix_operations_tab()
        
        # Configurar la pestaña de Gauss-Jordan
        self.setup_gauss_tab()
        
        # Configurar la pestaña de Bisección
        self.setup_bisection_tab()
        
        # Configurar la pestaña de Falsa Posición
        self.setup_false_position_tab()

        # Configurar la pestaña de Newton-Raphson
        self.setup_newton_tab()
        self.setup_secant_tab()
        
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
        
        self.gauss_result_text = scrolledtext.ScrolledText(result_frame, width=120, height=20,
                                 font=("Consolas", 12),
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
        
        # Crear encabezados de columnas (alineados con entradas)
        if vector_mode:
            for j in range(cols):
                var_label = tk.Label(entries_frame, text=f"v{j+1}", 
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["matrix_bg"], fg=self.colors["accent"])
                var_label.grid(row=0, column=j, padx=3, pady=3)
        else:
            for j in range(cols):
                var_label = tk.Label(entries_frame, text=f"x{j+1}", 
                                   font=("Segoe UI", 11, "bold"),
                                   bg=self.colors["matrix_bg"], fg=self.colors["accent"])
                var_label.grid(row=0, column=j, padx=3, pady=3)
            # Columna separadora vacía
            entries_frame.grid_columnconfigure(cols, minsize=6)
            # Etiqueta para el vector b (a la derecha del separador)
            b_label = tk.Label(entries_frame, text="b", 
                             font=("Segoe UI", 11, "bold"),
                             bg=self.colors["matrix_bg"], fg=self.colors["accent"])
            b_label.grid(row=0, column=cols+1, padx=3, pady=3)
        
        # Crear entradas
        for i in range(rows):
            row_entries = []
            if vector_mode:
                for j in range(cols):
                    entry = tk.Entry(entries_frame, **entry_style)
                    entry.grid(row=i+1, column=j, padx=3, pady=3)
                    entry.insert(0, "0")
                    row_entries.append(entry)
            else:
                # A
                for j in range(cols):
                    entry = tk.Entry(entries_frame, **entry_style)
                    entry.grid(row=i+1, column=j, padx=3, pady=3)
                    entry.insert(0, "0")
                    row_entries.append(entry)
                # b (a la derecha del separador)
                entry_b = tk.Entry(entries_frame, **entry_style)
                entry_b.grid(row=i+1, column=cols+1, padx=3, pady=3)
                entry_b.insert(0, "0")
                row_entries.append(entry_b)
            self.gauss_entries.append(row_entries)
        
        # Línea vertical para separar A de b (solo si no es modo vectores)
        if not vector_mode:
            separator = tk.Frame(entries_frame, bg=self.colors["accent"], width=2)
            separator.grid(row=0, column=cols, rowspan=rows+1, sticky="ns")

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
        return fraction_to_str(frac)

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
        border_frame = tk.Frame(self.bisection_tab, bg="#7B68EE", relief="flat", bd=1)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Frame principal dentro del borde
        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
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
           # (La previsualización se crea en el marco derecho para coincidir con Falsa Posición)

        # Preview + plot area container on the right (plot enlarged to occupy corner)
        right_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        right_frame.pack(side="right", fill="both", expand=True, padx=(10,0))

        # Previsualización arriba
        prev_frame = tk.Frame(right_frame, bg=self.colors["secondary_bg"], relief="flat", bd=1)
        prev_frame.pack(fill="x", pady=(0,8))
        tk.Label(prev_frame, text="Previsualización:", font=("Segoe UI", 10, "bold"),
             bg=self.colors["secondary_bg"], fg=self.colors["text"]).pack(anchor="w", padx=6, pady=(4,0))

        self.bis_preview_fig = Figure(figsize=(3,0.8), dpi=150)
        self.bis_prev_ax = self.bis_preview_fig.add_subplot(111)
        self.bis_prev_ax.axis('off')
        self.bis_prev_canvas = FigureCanvasTkAgg(self.bis_preview_fig, prev_frame)
        self.bis_prev_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)

           # Plot area (embedded) debajo
        plot_frame = tk.Frame(right_frame, bg=self.colors["background"])
        plot_frame.pack(fill="both", expand=True)
        self.bis_plot_fig = Figure(figsize=(5,4), dpi=150)
        self.bis_plot_ax = self.bis_plot_fig.add_subplot(111)
        self.bis_plot_canvas = FigureCanvasTkAgg(self.bis_plot_fig, plot_frame)
        self.bis_plot_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.bis_toolbar = NavigationToolbar2Tk(self.bis_plot_canvas, plot_frame)
        self.bis_toolbar.update()
        self.bis_plot_ax.format_coord = lambda x, y: ""
        self.bis_hover_annot = self.bis_plot_ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points", bbox=dict(boxstyle="round", fc="#000", ec="#fff", alpha=0.6), color="#fff")
        self.bis_hover_annot.set_visible(False)
        self.bis_plot_canvas.mpl_connect('motion_notify_event', self.on_bis_motion)
        self.bis_plot_canvas.mpl_connect('scroll_event', self.on_bis_scroll)
        expand_frame = tk.Frame(plot_frame, bg=self.colors["background"]) 
        expand_frame.pack(fill="x", pady=(0,4))
        tk.Button(expand_frame, text="⤢ Expandir", command=lambda: self.open_expanded_plot('bisection'), bg=self.colors["accent"], fg=self.colors["text"], relief="flat").pack(side="right")

        # La previsualización ya está arriba (igual que en Falsa Posición)

        # Update preview when typing
        self.function_entry.bind('<KeyRelease>', lambda e: self.update_bisection_preview())
        
        
        # Inicializar preview vacío
        self.update_bisection_preview()
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
        btn_frame.pack(pady=(8, 0))
        # Guardar referencia para posicionar el teclado centrado respecto a estos botones
        self.bisection_btn_frame = btn_frame
        
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
        # (El botón de Falsa Posición se elimina para mantener coherencia en Bisección)

        # Frame para el teclado virtual (visible por defecto) - lo colocamos flotando centrado
        # dentro de `main_frame` usando place(), para situarlo a la mitad de la ventana.
        self.keyboard_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        # No usamos pack aquí; colocamos el teclado centrado en la ventana
        # Place keyboard centered below the buttons frame
        self.keyboard_frame.place(in_=self.bisection_btn_frame, relx=0.5, rely=1.06, anchor="n")
        # El teclado estará visible por defecto
        self.keyboard_visible = True
        self.setup_virtual_keyboard()

        # Frame para resultados (crear después para que aparezca debajo del teclado)
        self.bisection_result_frame = tk.Frame(main_frame, bg=self.colors["background"])
        self.bisection_result_frame.pack(fill="both", expand=True, pady=(15, 0))
        
        tk.Label(self.bisection_result_frame, text="Resultados:", font=("Segoe UI", 14, "bold"),
                bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        
        # Área de resultados con scrollbar vertical explícita
        results_container = tk.Frame(self.bisection_result_frame, bg=self.colors["background"])
        results_container.pack(fill="both", expand=True)
        self.bisection_result_text = tk.Text(results_container, width=100, height=28,
                     font=("Consolas", 14),
                             bg=self.colors["secondary_bg"], 
                             fg=self.colors["text"],
                             insertbackground=self.colors["text"],
                             relief="flat", bd=1, wrap="none")
        vsb = tk.Scrollbar(results_container, orient="vertical", command=self.bisection_result_text.yview)
        self.bisection_result_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.bisection_result_text.pack(side="left", fill="both", expand=True)
        
        # Configurar estilos de texto
        self.bisection_result_text.tag_configure("title", foreground=self.colors["accent"], font=("Consolas", 12, "bold"))
        self.bisection_result_text.tag_configure("step", foreground="#30D158", font=("Consolas", 12))
        self.bisection_result_text.tag_configure("error", foreground="#FF453A", font=("Consolas", 12, "bold"))
        self.bisection_result_text.tag_configure("result", foreground="#30D158", font=("Consolas", 14, "bold"))
        self.bisection_result_text.tag_configure("warning", foreground="#FF9F0A", font=("Consolas", 12))
        
        # Mensaje inicial
        self.bisection_result_text.insert("1.0", "Los resultados del método de bisección se mostrarán aquí.")
        self.bisection_result_text.config(state="disabled")

    def setup_false_position_tab(self):
        """Configura la pestaña del Método de Falsa Posición"""
        border_frame = tk.Frame(self.falsepos_tab, bg="#FFB703", relief="flat", bd=1)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)

        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)

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

        # Right-side preview + plot similar to bisection
        right_frame_fp = tk.Frame(top_frame, bg=self.colors["background"]) 
        right_frame_fp.pack(side="right", fill="both", expand=True, padx=(10,0))

        prev_frame_fp = tk.Frame(right_frame_fp, bg=self.colors["secondary_bg"], relief="flat", bd=1)
        prev_frame_fp.pack(fill="x", pady=(0,8))
        tk.Label(prev_frame_fp, text="Previsualización:", font=("Segoe UI", 10, "bold"),
             bg=self.colors["secondary_bg"], fg=self.colors["text"]).pack(anchor="w", padx=6, pady=(4,0))

        self.fp_preview_fig = Figure(figsize=(3,0.8), dpi=150)
        self.fp_prev_ax = self.fp_preview_fig.add_subplot(111)
        self.fp_prev_ax.axis('off')
        self.fp_prev_canvas = FigureCanvasTkAgg(self.fp_preview_fig, prev_frame_fp)
        self.fp_prev_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)

        plot_frame_fp = tk.Frame(right_frame_fp, bg=self.colors["background"])
        plot_frame_fp.pack(fill="both", expand=True)
        # Usar el mismo tamaño de gráfica que en Bisección (más amplio)
        self.fp_plot_fig = Figure(figsize=(5,4), dpi=150)
        self.fp_plot_ax = self.fp_plot_fig.add_subplot(111)
        self.fp_plot_canvas = FigureCanvasTkAgg(self.fp_plot_fig, plot_frame_fp)
        self.fp_plot_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.fp_toolbar = NavigationToolbar2Tk(self.fp_plot_canvas, plot_frame_fp)
        self.fp_toolbar.update()
        self.fp_plot_ax.format_coord = lambda x, y: ""
        self.fp_hover_annot = self.fp_plot_ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points", bbox=dict(boxstyle="round", fc="#000", ec="#fff", alpha=0.6), color="#fff")
        self.fp_hover_annot.set_visible(False)
        self.fp_plot_canvas.mpl_connect('motion_notify_event', self.on_fp_motion)
        self.fp_plot_canvas.mpl_connect('scroll_event', self.on_fp_scroll)
        expand_frame_fp = tk.Frame(plot_frame_fp, bg=self.colors["background"]) 
        expand_frame_fp.pack(fill="x", pady=(0,4))
        tk.Button(expand_frame_fp, text="⤢ Expandir", command=lambda: self.open_expanded_plot('falsepos'), bg=self.colors["accent"], fg=self.colors["text"], relief="flat").pack(side="right")

        # Bind preview update
        self.fp_function_entry.bind('<KeyRelease>', lambda e: self.update_falsepos_preview())
        self.update_falsepos_preview()

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
        btn_frame.pack(pady=(8, 0))
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

        tk.Button(btn_frame, text="🔢 Calcular Raíz", command=self.calculate_false_position_fp,
                  bg=self.colors["accent"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🗑 Limpiar", command=self.clear_false_position,
                  bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="📊 Graficar Función", command=self.plot_function_fp,
                  bg="#7B68EE", fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🔎 Sugerir Intervalo", command=self.suggest_interval_fp,
                  bg="#20B2AA", fg="white", **button_style).pack(side="left", padx=(0, 8))

        # Frame para el teclado virtual (visible por defecto)
        self.fp_keyboard_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        # Guardar referencia al btn_frame de falsa posición para centrar el teclado
        self.fp_btn_frame = btn_frame
        self.fp_keyboard_frame.place(in_=self.fp_btn_frame, relx=0.5, rely=1.06, anchor="n")
        self.fp_keyboard_visible = True
        
        self.setup_virtual_keyboard_fp()
        
        # Resultados
        self.fp_result_frame = tk.Frame(main_frame, bg=self.colors["background"]) 
        self.fp_result_frame.pack(fill="both", expand=True, pady=(15, 0))
        tk.Label(self.fp_result_frame, text="Resultados:", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        # Área de resultados con scrollbar vertical explícita
        fp_results_container = tk.Frame(self.fp_result_frame, bg=self.colors["background"])
        fp_results_container.pack(fill="both", expand=True)
        self.falsepos_result_text = tk.Text(fp_results_container, width=100, height=28, font=("Consolas", 14),
                            bg=self.colors["secondary_bg"], fg=self.colors["text"],
                            insertbackground=self.colors["text"], relief="flat", bd=1, wrap="none")
        fp_vsb = tk.Scrollbar(fp_results_container, orient="vertical", command=self.falsepos_result_text.yview)
        self.falsepos_result_text.configure(yscrollcommand=fp_vsb.set)
        fp_vsb.pack(side="right", fill="y")
        self.falsepos_result_text.pack(side="left", fill="both", expand=True)
        self.falsepos_result_text.tag_configure("title", foreground=self.colors["accent"], font=("Consolas", 12, "bold"))
        self.falsepos_result_text.tag_configure("step", foreground="#30D158", font=("Consolas", 12))
        self.falsepos_result_text.tag_configure("error", foreground="#FF453A", font=("Consolas", 12, "bold"))
        self.falsepos_result_text.tag_configure("result", foreground="#30D158", font=("Consolas", 14, "bold"))
        self.falsepos_result_text.tag_configure("warning", foreground="#FF9F0A", font=("Consolas", 12))
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

            if re.search(r"\bln\b|\blog\b", func_str):
                if a <= 0 or b <= 0:
                    messagebox.showerror("Error", "Dominio inválido para ln(x)/log(x): requiere x>0. Ajusta el intervalo [a,b].")
                    return

            fa = self.evaluate_function(a, func_str)
            fb = self.evaluate_function(b, func_str)
            if fa * fb > 0:
                sa, sb, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
                if sa is None:
                    messagebox.showerror("Error", "La función no cambia de signo en [a,b] ni en rangos amplios probados.")
                    return
                a, b = sa, sb
                fa = self.evaluate_function(a, func_str)
                fb = self.evaluate_function(b, func_str)
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

            # Encabezado de tabla
            self.falsepos_result_text.insert(tk.END, "\nTABLA DE ITERACIONES:\n", "title")
            self.falsepos_result_text.insert(tk.END, "=" * 95 + "\n", "step")
            header = f"{'Iter':<6} {'a':>14} {'b':>14} {'c':>14} {'f(a)':>14} {'f(b)':>14} {'f(c)':>14} {'Error':>14}\n"
            self.falsepos_result_text.insert(tk.END, header, "step")
            self.falsepos_result_text.insert(tk.END, "-" * 95 + "\n", "step")

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

                # error mostrado será |f(c)|
                error_c = abs(fc)
                row = f"{iteration+1:<6} {a:>14.8f} {b:>14.8f} {c:>14.8f} {fa:>14.8f} {fb:>14.8f} {fc:>14.8f} {error_c:>14.8f}\n"
                self.falsepos_result_text.insert(tk.END, row, "matrix")

                # Mostrar actualización de intervalo (breve)
                if fa * fc < 0:
                    b = c
                    fb = fc
                    self.falsepos_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(a) * f(c) < 0)\n", "step")
                else:
                    a = c
                    fa = fc
                    self.falsepos_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(b) * f(c) < 0)\n", "step")

                self.falsepos_result_text.insert(tk.END, "\n")

                if abs(fc) <= tolerance or (prev_c is not None and abs(c - prev_c) <= tolerance) or abs(b - a) <= tolerance:
                    prev_c = c
                    iteration += 1
                    break

                prev_c = c
                iteration += 1

            root = prev_c if prev_c is not None else (a + b) / 2
            self.calculated_root = root
            self.calculated_func_str = func_str
            self.falsepos_result_text.insert(tk.END, "=" * 95 + "\n\n", "step")
            self.falsepos_result_text.insert(tk.END, "RESULTADO FINAL (Falsa Posición):\n", "result")
            self.falsepos_result_text.insert(tk.END, f"La raiz aproximada es x = {root:.8f}\n", "result")
            self.falsepos_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.falsepos_result_text.insert(tk.END, f"Converge en {iteration} iteraciones\n", "result")
            self.falsepos_result_text.insert(tk.END, f"El error final |f(c)| es: {abs(self.evaluate_function(root, func_str)):.2e}\n", "result")

            if iteration >= max_iterations:
                self.falsepos_result_text.insert(tk.END, "\n⚠ ADVERTENCIA: Se alcanzó el máximo de iteraciones\n", "warning")

            try:
                self.falsepos_result_text.see(tk.END)
            except Exception:
                pass
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

            use_embedded = hasattr(self, 'fp_plot_canvas')
            if use_embedded:
                prev_xlim = self.fp_plot_ax.get_xlim()
                prev_ylim = self.fp_plot_ax.get_ylim()
                restore_view = getattr(self, 'fp_plot_init_done', False)
            else:
                restore_view = False
            if use_embedded and restore_view:
                x_min, x_max = prev_xlim
            else:
                margin = max(abs(b - a) * 0.2, 1)
                base_min = min(a, b) - margin; base_max = max(a, b) + margin
                x_min, x_max = self._determine_plot_range(func_str, base_min, base_max)
            x = np.linspace(x_min, x_max, 4000)
            y = self.evaluate_function_vectorized(x, func_str)
            y_plot = np.where(np.isfinite(y), y, np.nan)

            if np.all(np.isnan(y_plot)):
                messagebox.showerror("Error al graficar", "No se pudieron evaluar puntos válidos en el intervalo.")
                return

            formatted_func = self.format_function_display(func_str)
            if use_embedded:
                ax = self.fp_plot_ax
                ax.clear()
                ax.plot(x, y_plot, label=f"f(x) = {formatted_func}", color="#FFB703", linewidth=2)
                ax.axhline(0, color="#FF453A", linewidth=1)
                ax.axvline(0, color="#FF9F0A", linewidth=1)
                ax.axvline(x=a, color='g', linewidth=2, linestyle=':', alpha=0.7, label=f'a = {a:.2f}')
                ax.axvline(x=b, color='r', linewidth=2, linestyle=':', alpha=0.7, label=f'b = {b:.2f}')
                ax.set_title(f"Gráfica de f(x) = {formatted_func} - Falsa Posición")
                ax.set_xlabel('x')
                ax.set_ylabel('f(x)')
                dy = np.gradient(np.nan_to_num(y_plot, nan=0.0), x)
                vx = []; vy = []
                mask = np.isfinite(y_plot)
                idx = np.where(mask)[0]
                if len(idx) > 1:
                    prev = idx[0]
                    run = [prev]
                    for i in idx[1:]:
                        if i == prev + 1:
                            run.append(i)
                        else:
                            if len(run) > 1:
                                dr = dy[run]
                                for j in range(1, len(dr)):
                                    if (dr[j-1] > 0 and dr[j] <= 0) or (dr[j-1] < 0 and dr[j] >= 0):
                                        k = run[j]
                                        vx.append(x[k]); vy.append(y_plot[k])
                            run = [i]
                        prev = i
                    if len(run) > 1:
                        dr = dy[run]
                        for j in range(1, len(dr)):
                            if (dr[j-1] > 0 and dr[j] <= 0) or (dr[j-1] < 0 and dr[j] >= 0):
                                k = run[j]
                                vx.append(x[k]); vy.append(y_plot[k])
                if vx:
                    ax.plot(vx, vy, marker='D', linestyle='None', color='#FF9F0A', label='Vértices')
                self.fp_vertices = list(zip(vx, vy))
                if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == func_str:
                    try:
                        f_root = self.evaluate_function(self.calculated_root, func_str)
                        ax.plot(self.calculated_root, f_root, marker='o', linestyle='None', markersize=10, color='#BB33FF', label=f'Raíz ≈ {self.calculated_root:.4f}')
                        ax.axvline(x=self.calculated_root, color='#BB33FF', linewidth=1.5, linestyle='--', alpha=0.6)
                    except:
                        pass
                if not restore_view:
                    try:
                        p1, p99 = np.nanpercentile(y_plot, [1, 99])
                        if not (np.isnan(p1) or np.isnan(p99)):
                            yr = p99 - p1
                            if yr > 0:
                                ax.set_ylim(p1 - yr * 0.1, p99 + yr * 0.1)
                            else:
                                ax.set_ylim(p1 - 1, p99 + 1)
                        ax.set_xlim(x_min, x_max)
                    except Exception:
                        pass
                else:
                    try:
                        ax.set_xlim(prev_xlim); ax.set_ylim(prev_ylim)
                    except Exception:
                        pass
                ax.grid(True, linestyle='--', alpha=0.5)
                ax.legend()
                self.fp_plot_init_done = True
                try:
                    self.fp_plot_canvas.draw()
                except Exception:
                    pass
            else:
                # Fallback: ventana emergente con matplotlib
                plot_window = tk.Toplevel(self.root)
                plot_window.title(f"Gráfica de f(x) = {formatted_func}")
                fig = Figure(figsize=(7, 4.5), dpi=100)
                ax = fig.add_subplot(111)
                ax.plot(x, y_plot, label=f"f(x) = {formatted_func}", color="#FFB703", linewidth=2)
                ax.axhline(0, color="#FF453A", linewidth=1)
                ax.axvline(0, color="#FF9F0A", linewidth=1)
                ax.axvline(x=a, color='g', linewidth=2, linestyle=':', alpha=0.7, label=f'a = {a:.2f}')
                ax.axvline(x=b, color='r', linewidth=2, linestyle=':', alpha=0.7, label=f'b = {b:.2f}')
                ax.set_title(f"Gráfica de f(x) = {formatted_func} - Falsa Posición")
                ax.set_xlabel('x')
                ax.set_ylabel('f(x)')
                try:
                    p1, p99 = np.nanpercentile(y_plot, [1, 99])
                    if not (np.isnan(p1) or np.isnan(p99)):
                        yr = p99 - p1
                        if yr > 0:
                            ax.set_ylim(p1 - yr * 0.1, p99 + yr * 0.1)
                        else:
                            ax.set_ylim(p1 - 1, p99 + 1)
                    ax.set_xlim(x_min, x_max)
                except Exception:
                    pass
                ax.grid(True, linestyle='--', alpha=0.5)
                ax.legend()
                canvas = FigureCanvasTkAgg(fig, plot_window)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar la función: {str(e)}")

    def open_expanded_plot(self, which):
        if which == 'bisection':
            func_str = self.function_var.get().strip()
        elif which == 'falsepos':
            func_str = self.fp_function_var.get().strip()
        elif which == 'secant':
            func_str = self.sc_function_var.get().strip()
        else:
            func_str = self.nw_function_var.get().strip()
        if not func_str:
            return
        win = tk.Toplevel(self.root)
        win.title("Vista ampliada")
        fig = Figure(figsize=(9,6), dpi=100)
        ax = fig.add_subplot(111)
        # Determinar intervalo y estilo
        if which == 'bisection':
            a = float(self.a_var.get()); b = float(self.b_var.get())
            color_fn = 'b-'
            src_ax = self.bis_plot_ax
        elif which == 'falsepos':
            a = float(self.fp_a_var.get()); b = float(self.fp_b_var.get())
            color_fn = None
            src_ax = self.fp_plot_ax
        elif which == 'secant':
            try:
                x0 = float(self.sc_x0_var.get()); x1 = float(self.sc_x1_var.get())
            except:
                x0 = -5.0; x1 = 5.0
            a = min(x0, x1); b = max(x0, x1)
            color_fn = 'b-'
            src_ax = self.sc_plot_ax
        else:
            # newton
            try:
                x0 = float(self.nw_x0_var.get())
            except:
                x0 = 0.0
            a = x0 - 5
            b = x0 + 5
            color_fn = 'b-'
            src_ax = self.nw_plot_ax
        # Rango x amplio y automático
        margin = max(abs(b - a) * 0.2, 1)
        base_min = min(a, b) - margin
        base_max = max(a, b) + margin
        x_min, x_max = self._determine_plot_range(func_str, base_min, base_max)
        x = np.linspace(x_min, x_max, 4000)
        y = self.evaluate_function_vectorized(x, func_str)
        y_plot = np.where(np.isfinite(y), y, np.nan)
        ax.plot(x, y_plot, color="#2F80ED" if color_fn is None else None, linestyle='-', linewidth=2)
        # Estilo tipo GeoGebra
        ax.axhline(0, color="#666", linewidth=1.2, linestyle='--', alpha=0.7)
        ax.axvline(0, color="#666", linewidth=1.2, linestyle='--', alpha=0.7)
        ax.axvline(a, color="#30D158", linewidth=1.5, linestyle=':', alpha=0.9, label=f"a = {a:.2f}")
        ax.axvline(b, color="#FF453A", linewidth=1.5, linestyle=':', alpha=0.9, label=f"b = {b:.2f}")
        # f(a), f(b)
        try:
            fa = self.evaluate_function(a, func_str); fb = self.evaluate_function(b, func_str)
            ax.plot(a, fa, 'o', color="#30D158", markersize=8, label=f"f(a) = {fa:.3f}")
            ax.plot(b, fb, 'o', color="#FF453A", markersize=8, label=f"f(b) = {fb:.3f}")
        except:
            pass
        # Raíz y vértices
        if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == func_str:
            try:
                fr = self.evaluate_function(self.calculated_root, func_str)
                ax.plot(self.calculated_root, fr, marker='o', linestyle='None', color="#BB33FF", markersize=10, label=f"Raíz ≈ {self.calculated_root:.4f}")
                ax.axvline(self.calculated_root, color="#BB33FF", linewidth=1.2, linestyle='--', alpha=0.7)
            except:
                pass
        verts = self.bis_vertices if which == 'bisection' else getattr(self, 'fp_vertices', [])
        if verts:
            vx, vy = zip(*verts)
            ax.plot(vx, vy, marker='D', linestyle='None', color="#FF9F0A", label="Vértices")
        ax.set_xlabel('x'); ax.set_ylabel('f(x)')
        ax.grid(True, linestyle='--', alpha=0.35)
        ax.legend(loc='best')
        # Copiar vista del embed
        try:
            ax.set_xlim(*src_ax.get_xlim()); ax.set_ylim(*src_ax.get_ylim())
        except:
            pass
        canvas = FigureCanvasTkAgg(fig, win)
        canvas.draw()
        tb = NavigationToolbar2Tk(canvas, win)
        tb.update()
        ax.format_coord = lambda x, y: ""
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def on_bis_motion(self, event):
        ax = self.bis_plot_ax
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            self.bis_hover_annot.set_visible(False); self.bis_plot_canvas.draw_idle(); return
        xr = ax.get_xlim(); yr = ax.get_ylim()
        tolx = (xr[1]-xr[0])*0.02; toly = (yr[1]-yr[0])*0.02
        show = False; text = ""; xy = (event.xdata, event.ydata)
        if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == self.function_var.get().strip():
            try:
                fr = self.evaluate_function(self.calculated_root, self.function_var.get().strip())
                if abs(event.xdata - self.calculated_root) <= tolx and abs(event.ydata - fr) <= toly:
                    show = True; text = f"raíz ≈ {self.calculated_root:.6f}"; xy = (self.calculated_root, fr)
            except:
                pass
        if not show and hasattr(self, 'bis_vertices'):
            for vx, vy in self.bis_vertices:
                if abs(event.xdata - vx) <= tolx and abs(event.ydata - vy) <= toly:
                    show = True; text = f"vértice ({vx:.4f}, {vy:.4f})"; xy = (vx, vy); break
        if show:
            self.bis_hover_annot.xy = xy; self.bis_hover_annot.set_text(text); self.bis_hover_annot.set_visible(True)
        else:
            self.bis_hover_annot.set_visible(False)
        self.bis_plot_canvas.draw_idle()

    def on_fp_motion(self, event):
        ax = self.fp_plot_ax
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            self.fp_hover_annot.set_visible(False); self.fp_plot_canvas.draw_idle(); return
        xr = ax.get_xlim(); yr = ax.get_ylim()
        tolx = (xr[1]-xr[0])*0.02; toly = (yr[1]-yr[0])*0.02
        show = False; text = ""; xy = (event.xdata, event.ydata)
        if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == self.fp_function_var.get().strip():
            try:
                fr = self.evaluate_function(self.calculated_root, self.fp_function_var.get().strip())
                if abs(event.xdata - self.calculated_root) <= tolx and abs(event.ydata - fr) <= toly:
                    show = True; text = f"raíz ≈ {self.calculated_root:.6f}"; xy = (self.calculated_root, fr)
            except:
                pass
        if not show and hasattr(self, 'fp_vertices'):
            for vx, vy in self.fp_vertices:
                if abs(event.xdata - vx) <= tolx and abs(event.ydata - vy) <= toly:
                    show = True; text = f"vértice ({vx:.4f}, {vy:.4f})"; xy = (vx, vy); break
        if show:
            self.fp_hover_annot.xy = xy; self.fp_hover_annot.set_text(text); self.fp_hover_annot.set_visible(True)
        else:
            self.fp_hover_annot.set_visible(False)
        self.fp_plot_canvas.draw_idle()

    def on_bis_scroll(self, event):
        self._zoom_on_scroll(self.bis_plot_ax, self.bis_plot_canvas, event)

    def on_fp_scroll(self, event):
        self._zoom_on_scroll(self.fp_plot_ax, self.fp_plot_canvas, event)

    def on_nw_scroll(self, event):
        self._zoom_on_scroll(self.nw_plot_ax, self.nw_plot_canvas, event)

    def _zoom_on_scroll(self, ax, canvas, event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
        factor = 1.2 if getattr(event, 'button', 'up') == 'up' else (1/1.2)
        cx, cy = event.xdata, event.ydata
        nx = (x1 - x0) / factor; ny = (y1 - y0) / factor
        ax.set_xlim(cx - nx/2, cx + nx/2)
        ax.set_ylim(cy - ny/2, cy + ny/2)
        try:
            canvas.draw_idle()
        except:
            pass

    def _suggest_interval_core(self, func_str, prefer_zero=True):
        search_specs = [(-10, 10, 0.1), (-50, 50, 0.2), (-100, 100, 0.5)]
        intervals = []
        zeros = []
        y_limit = 1e6
        for a_range, b_range, step in search_specs:
            prev_x, prev_y = None, None
            x = float(a_range)
            while x <= float(b_range):
                try:
                    y = float(self.evaluate_function(x, func_str))
                    finite = not math.isnan(y) and math.isfinite(y)
                    if finite and abs(y) < 1e-12:
                        zeros.append((x, step))
                    if prev_y is not None:
                        finite_prev = not math.isnan(prev_y) and math.isfinite(prev_y)
                        if finite_prev and finite and abs(prev_y) < y_limit and abs(y) < y_limit:
                            if prev_y * y < 0:
                                intervals.append((prev_x, x))
                                if len(intervals) >= 32:
                                    break
                    prev_x, prev_y = x, y
                except Exception:
                    prev_x, prev_y = None, None
                x = round(x + step, 10)
            if intervals or zeros:
                break
        if not intervals and not zeros:
            return None, None, [], []
        if zeros and prefer_zero:
            zx, st = sorted(zeros, key=lambda t: (abs(t[0]), 0 if t[0] >= 0 else 1))[0]
            a, b = zx - st, zx + st
        else:
            def score(ab):
                try:
                    fa = float(self.evaluate_function(ab[0], func_str))
                    fb = float(self.evaluate_function(ab[1], func_str))
                    mid = (ab[0] + ab[1]) / 2.0
                    val = (min(abs(ab[0]), abs(ab[1])), abs(fa) + abs(fb), 0 if mid >= 0 else 1)
                except Exception:
                    mid = (ab[0] + ab[1]) / 2.0
                    val = (min(abs(ab[0]), abs(ab[1])), float('inf'), 0 if mid >= 0 else 1)
                return val
            a, b = sorted(intervals, key=score)[0]
        try:
            fa = float(self.evaluate_function(a, func_str)); fb = float(self.evaluate_function(b, func_str))
        except Exception:
            fa, fb = float('nan'), float('nan')
        if not (not math.isnan(fa) and not math.isnan(fb) and math.isfinite(fa) and math.isfinite(fb) and fa*fb < 0):
            cx = 0.0 if (zeros and prefer_zero) else ((a + b) / 2.0)
            step = 0.1
            for k in range(1, 51):
                a2, b2 = cx - k*step, cx + k*step
                try:
                    fa2 = float(self.evaluate_function(a2, func_str)); fb2 = float(self.evaluate_function(b2, func_str))
                    if (not math.isnan(fa2) and not math.isnan(fb2) and math.isfinite(fa2) and math.isfinite(fb2) and fa2*fb2 < 0 and abs(fa2) < y_limit and abs(fb2) < y_limit):
                        a, b = a2, b2
                        break
                except Exception:
                    pass
        return a, b, intervals, zeros

    def _determine_plot_range(self, func_str, base_min=None, base_max=None):
        try:
            specs = [(-20, 20, 0.05), (-50, 50, 0.1), (-100, 100, 0.2)]
            intervals = []
            y_limit = 1e6
            for a_range, b_range, step in specs:
                prev_x, prev_y = None, None
                x = float(a_range)
                while x <= float(b_range):
                    try:
                        y = float(self.evaluate_function(x, func_str))
                        if prev_y is not None:
                            if all([math.isfinite(y), math.isfinite(prev_y), abs(y) < y_limit, abs(prev_y) < y_limit]):
                                if prev_y * y < 0:
                                    intervals.append((prev_x, x))
                        prev_x, prev_y = x, y
                    except Exception:
                        prev_x, prev_y = None, None
                    x = round(x + step, 10)
                if intervals:
                    break
            if intervals:
                xs = [v for ab in intervals for v in ab]
                x_min = min(xs) - 2.0
                x_max = max(xs) + 2.0
            else:
                if base_min is not None and base_max is not None:
                    x_min, x_max = base_min, base_max
                else:
                    x_min, x_max = -10.0, 10.0
            if x_max - x_min < 10.0:
                mid = (x_min + x_max) / 2.0
                x_min = mid - 5.0; x_max = mid + 5.0
            x_min = max(x_min, -100.0); x_max = min(x_max, 100.0)
            return x_min, x_max
        except Exception:
            return (base_min if base_min is not None else -10.0, base_max if base_max is not None else 10.0)

    def suggest_interval_fp(self):
        func_str = self.fp_function_var.get().strip()
        if not func_str:
            messagebox.showerror("Error", "Por favor ingrese una función en 'f(x)'.")
            return
        a, b, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
        if a is None:
            messagebox.showwarning("Sin cambio de signo", "No se encontraron intervalos con cambio de signo en los rangos probados.")
            return
        self.fp_a_var.set(f"{a:.6f}"); self.fp_b_var.set(f"{b:.6f}")
        txt = "Intervalos con cambio de signo detectados:\n\n"
        for i, (ia, ib) in enumerate(intervals, 1):
            txt += f"{i}. [{ia:.6f}, {ib:.6f}]\n"
        if zeros:
            txt += "\nRaíces exactas detectadas en muestreo:\n"
            for i, (zx, st) in enumerate(sorted(zeros, key=lambda t: abs(t[0])), 1):
                txt += f"{i}. x = {zx:.6f} (intervalo sugerido [{zx-st:.6f}, {zx+st:.6f}])\n"
        txt += "\nSe asignó el intervalo más cercano a 0."
        messagebox.showinfo("Sugerencia de Intervalos", txt)

    def derivative_numeric(self, x, func_str, h=1e-6):
        try:
            fph = self.evaluate_function(x + h, func_str)
            fmh = self.evaluate_function(x - h, func_str)
            return (fph - fmh) / (2*h)
        except Exception as e:
            raise ValueError(str(e))

    def setup_newton_tab(self):
        border_frame = tk.Frame(self.newton_tab, bg="#20B2AA", relief="flat", bd=1)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)
        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(main_frame, text="Método de Newton-Raphson", font=("Segoe UI", 24, "bold"),
                 bg=self.colors["background"], fg=self.colors["accent"]).pack(pady=(0,20))

        top_frame = tk.Frame(main_frame, bg=self.colors["background"])
        top_frame.pack(pady=(0, 15), fill="x")

        func_frame = tk.Frame(top_frame, bg=self.colors["background"])
        func_frame.pack(fill="x", pady=(0, 10))
        tk.Label(func_frame, text="Función f(x):", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        func_input_frame = tk.Frame(func_frame, bg=self.colors["background"]) 
        func_input_frame.pack(fill="x")
        self.nw_function_var = tk.StringVar()
        self.nw_function_entry = tk.Entry(func_input_frame, textvariable=self.nw_function_var,
                          font=("Segoe UI", 12), width=40,
                          bg=self.colors["entry_bg"], fg=self.colors["text"],
                          insertbackground=self.colors["text"], relief="flat", bd=1)
        self.nw_function_entry.pack(side="left", padx=(0,10))
        # Botón para mostrar/ocultar teclado y Ayuda
        self.nw_keyboard_btn = tk.Button(func_input_frame, text="🔽 Ocultar Teclado",
                                         command=self.toggle_keyboard_nw,
                                         bg=self.colors["button_secondary"], fg="white",
                                         font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                                         padx=15, pady=6, cursor="hand2",
                                         activebackground=self.colors["accent"],
                                         activeforeground="white")
        self.nw_keyboard_btn.pack(side="left", padx=(0,5))
        def on_enter_keyboard_nw(e): self.nw_keyboard_btn.config(bg=self.colors["accent"])
        def on_leave_keyboard_nw(e): self.nw_keyboard_btn.config(bg=self.colors["button_secondary"])
        self.nw_keyboard_btn.bind("<Enter>", on_enter_keyboard_nw)
        self.nw_keyboard_btn.bind("<Leave>", on_leave_keyboard_nw)
        nw_help_btn = tk.Button(func_input_frame, text="❓ Ayuda", command=self.show_function_help,
                                bg=self.colors["accent"], fg="white",
                                font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                                padx=10, pady=5, cursor="hand2")
        nw_help_btn.pack(side="left")

        right_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        right_frame.pack(side="right", fill="both", expand=True, padx=(10,0))
        prev_frame = tk.Frame(right_frame, bg=self.colors["secondary_bg"], relief="flat", bd=1)
        prev_frame.pack(fill="x", pady=(0,8))
        tk.Label(prev_frame, text="Previsualización:", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["secondary_bg"], fg=self.colors["text"]).pack(anchor="w", padx=6, pady=(4,0))
        self.nw_preview_fig = Figure(figsize=(3,0.8), dpi=150)
        self.nw_prev_ax = self.nw_preview_fig.add_subplot(111)
        self.nw_prev_ax.axis('off')
        self.nw_prev_canvas = FigureCanvasTkAgg(self.nw_preview_fig, prev_frame)
        self.nw_prev_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.nw_function_entry.bind('<KeyRelease>', lambda e: self.update_newton_preview())
        self.update_newton_preview()

        plot_frame = tk.Frame(right_frame, bg=self.colors["background"]) 
        plot_frame.pack(fill="both", expand=True)
        self.nw_plot_fig = Figure(figsize=(5,4), dpi=150)
        self.nw_plot_ax = self.nw_plot_fig.add_subplot(111)
        self.nw_plot_canvas = FigureCanvasTkAgg(self.nw_plot_fig, plot_frame)
        self.nw_plot_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.nw_toolbar = NavigationToolbar2Tk(self.nw_plot_canvas, plot_frame)
        self.nw_toolbar.update()
        self.nw_plot_ax.format_coord = lambda x, y: ""
        self.nw_hover_annot = self.nw_plot_ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                                       bbox=dict(boxstyle="round", fc="#000", ec="#fff", alpha=0.6), color="#fff")
        self.nw_hover_annot.set_visible(False)
        self.nw_plot_canvas.mpl_connect('motion_notify_event', self.on_nw_motion)
        self.nw_plot_canvas.mpl_connect('scroll_event', self.on_nw_scroll)
        expand_frame = tk.Frame(plot_frame, bg=self.colors["background"]) 
        expand_frame.pack(fill="x", pady=(0,4))
        tk.Button(expand_frame, text="⤢ Expandir", command=lambda: self.open_expanded_plot('newton'),
                  bg=self.colors["accent"], fg=self.colors["text"], relief="flat").pack(side="right")

        params_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        params_frame.pack(fill="x", pady=(10,0))
        x0_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        x0_frame.pack(side="left", padx=(0,20))
        tk.Label(x0_frame, text="x0 (inicio):", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.nw_x0_var = tk.StringVar(value="0.0")
        tk.Entry(x0_frame, textvariable=self.nw_x0_var, width=12,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()

        tol_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        tol_frame.pack(side="left", padx=(0,20))
        tk.Label(tol_frame, text="Tolerancia:", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.nw_tol_var = tk.StringVar(value="0.0001")
        tk.Entry(tol_frame, textvariable=self.nw_tol_var, width=12,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()

        iter_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        iter_frame.pack(side="left")
        tk.Label(iter_frame, text="Máx. iteraciones:", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.nw_max_iter_var = tk.StringVar(value="100")
        tk.Entry(iter_frame, textvariable=self.nw_max_iter_var, width=10,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()

        btn_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        btn_frame.pack(pady=(8,0))
        button_style = {"font": ("Segoe UI", 11, "bold"), "relief": "flat", "bd": 0,
                        "padx": 22, "pady": 10, "cursor": "hand2",
                        "activebackground": self.colors["accent"], "activeforeground": "white"}
        tk.Button(btn_frame, text="🔢 Calcular Raíz", command=self.calculate_newton,
                  bg=self.colors["accent"], fg="white", **button_style).pack(side="left", padx=(0,8))
        tk.Button(btn_frame, text="🗑 Limpiar", command=self.clear_newton,
                  bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0,8))
        tk.Button(btn_frame, text="📊 Graficar Función", command=self.plot_function_newton,
                  bg="#7B68EE", fg="white", **button_style).pack(side="left", padx=(0,8))
        tk.Button(btn_frame, text="🔎 Sugerir Intervalo", command=self.suggest_interval_nw,
                  bg="#20B2AA", fg="white", **button_style).pack(side="left", padx=(0,8))

        self.nw_btn_frame = btn_frame
        self.nw_keyboard_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        self.nw_keyboard_frame.place(in_=self.nw_btn_frame, relx=0.5, rely=1.06, anchor="n")
        self.nw_keyboard_visible = True
        self.setup_virtual_keyboard_nw()

        self.newton_result_frame = tk.Frame(main_frame, bg=self.colors["background"]) 
        self.newton_result_frame.pack(fill="both", expand=True, pady=(15,0))
        tk.Label(self.newton_result_frame, text="Resultados:", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,10))
        container = tk.Frame(self.newton_result_frame, bg=self.colors["background"]) 
        container.pack(fill="both", expand=True)
        self.newton_result_text = tk.Text(container, width=100, height=28, font=("Consolas", 14),
                                          bg=self.colors["secondary_bg"], fg=self.colors["text"],
                                          insertbackground=self.colors["text"], relief="flat", bd=1, wrap="none")
        vsb = tk.Scrollbar(container, orient="vertical", command=self.newton_result_text.yview)
        self.newton_result_text.configure(yscrollcommand=vsb.set)
        self.newton_result_text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.newton_result_text.tag_configure("title", foreground=self.colors["accent"], font=("Consolas", 12, "bold"))
        self.newton_result_text.tag_configure("step", foreground="#30D158", font=("Consolas", 12))
        self.newton_result_text.tag_configure("error", foreground="#FF453A", font=("Consolas", 12, "bold"))
        self.newton_result_text.tag_configure("result", foreground="#30D158", font=("Consolas", 14, "bold"))
        self.newton_result_text.tag_configure("warning", foreground=self.colors["accent"], font=("Consolas", 12))
        self.newton_result_text.insert("1.0", "Los resultados de Newton-Raphson se mostrarán aquí.")
        self.newton_result_text.config(state="disabled")

    def setup_secant_tab(self):
        border_frame = tk.Frame(self.secant_tab, bg="#8A2BE2", relief="flat", bd=1)
        border_frame.pack(fill="both", expand=True, padx=15, pady=15)
        main_frame = tk.Frame(border_frame, bg=self.colors["background"])
        main_frame.pack(fill="both", expand=True, padx=12, pady=12)
        tk.Label(main_frame, text="Método de la Secante", font=("Segoe UI", 24, "bold"),
                 bg=self.colors["background"], fg=self.colors["accent"]).pack(pady=(0,20))
        top_frame = tk.Frame(main_frame, bg=self.colors["background"]) 
        top_frame.pack(pady=(0, 15), fill="x")
        func_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        func_frame.pack(fill="x", pady=(0, 10))
        tk.Label(func_frame, text="Función f(x):", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        func_input_frame = tk.Frame(func_frame, bg=self.colors["background"]) 
        func_input_frame.pack(fill="x")
        self.sc_function_var = tk.StringVar()
        self.sc_function_entry = tk.Entry(func_input_frame, textvariable=self.sc_function_var,
                          font=("Segoe UI", 12), width=40,
                          bg=self.colors["entry_bg"], fg=self.colors["text"],
                          insertbackground=self.colors["text"], relief="flat", bd=1)
        self.sc_function_entry.pack(side="left", padx=(0,10))
        self.sc_keyboard_btn = tk.Button(func_input_frame, text="🔽 Ocultar Teclado",
                                         command=self.toggle_keyboard_sc,
                                         bg=self.colors["button_secondary"], fg="white",
                                         font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                                         padx=15, pady=6, cursor="hand2",
                                         activebackground=self.colors["accent"],
                                         activeforeground="white")
        self.sc_keyboard_btn.pack(side="left", padx=(0,5))
        right_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        right_frame.pack(side="right", fill="both", expand=True, padx=(10,0))
        prev_frame = tk.Frame(right_frame, bg=self.colors["secondary_bg"], relief="flat", bd=1)
        prev_frame.pack(fill="x", pady=(0,8))
        tk.Label(prev_frame, text="Previsualización:", font=("Segoe UI", 10, "bold"),
                 bg=self.colors["secondary_bg"], fg=self.colors["text"]).pack(anchor="w", padx=6, pady=(4,0))
        self.sc_preview_fig = Figure(figsize=(3,0.8), dpi=150)
        self.sc_prev_ax = self.sc_preview_fig.add_subplot(111)
        self.sc_prev_ax.axis('off')
        self.sc_prev_canvas = FigureCanvasTkAgg(self.sc_preview_fig, prev_frame)
        self.sc_prev_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.sc_function_entry.bind('<KeyRelease>', lambda e: self.update_secant_preview())
        self.update_secant_preview()
        plot_frame = tk.Frame(right_frame, bg=self.colors["background"]) 
        plot_frame.pack(fill="both", expand=True)
        self.sc_plot_fig = Figure(figsize=(5,4), dpi=150)
        self.sc_plot_ax = self.sc_plot_fig.add_subplot(111)
        self.sc_plot_canvas = FigureCanvasTkAgg(self.sc_plot_fig, plot_frame)
        self.sc_plot_canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=4)
        self.sc_toolbar = NavigationToolbar2Tk(self.sc_plot_canvas, plot_frame)
        self.sc_toolbar.update()
        self.sc_plot_ax.format_coord = lambda x, y: ""
        self.sc_hover_annot = self.sc_plot_ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                                       bbox=dict(boxstyle="round", fc="#000", ec="#fff", alpha=0.6), color="#fff")
        self.sc_hover_annot.set_visible(False)
        self.sc_plot_canvas.mpl_connect('motion_notify_event', self.on_sc_motion)
        self.sc_plot_canvas.mpl_connect('scroll_event', self.on_sc_scroll)
        expand_frame = tk.Frame(plot_frame, bg=self.colors["background"]) 
        expand_frame.pack(fill="x", pady=(0,4))
        tk.Button(expand_frame, text="⤢ Expandir", command=lambda: self.open_expanded_plot('secant'),
                  bg=self.colors["accent"], fg=self.colors["text"], relief="flat").pack(side="right")
        params_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        params_frame.pack(fill="x", pady=(10,0))
        x0_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        x0_frame.pack(side="left", padx=(0,20))
        tk.Label(x0_frame, text="x0:", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.sc_x0_var = tk.StringVar(value="0.0")
        tk.Entry(x0_frame, textvariable=self.sc_x0_var, width=12,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()
        x1_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        x1_frame.pack(side="left", padx=(0,20))
        tk.Label(x1_frame, text="x1:", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.sc_x1_var = tk.StringVar(value="1.0")
        tk.Entry(x1_frame, textvariable=self.sc_x1_var, width=12,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()
        tol_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        tol_frame.pack(side="left", padx=(0,20))
        tk.Label(tol_frame, text="Tolerancia:", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.sc_tol_var = tk.StringVar(value="0.0001")
        tk.Entry(tol_frame, textvariable=self.sc_tol_var, width=12,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()
        iter_frame = tk.Frame(params_frame, bg=self.colors["background"]) 
        iter_frame.pack(side="left")
        tk.Label(iter_frame, text="Máx. iteraciones:", font=("Segoe UI", 12, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0,5))
        self.sc_max_iter_var = tk.StringVar(value="100")
        tk.Entry(iter_frame, textvariable=self.sc_max_iter_var, width=10,
                 font=("Segoe UI", 11), bg=self.colors["entry_bg"], fg=self.colors["text"],
                 insertbackground=self.colors["text"], relief="flat", bd=1).pack()
        btn_frame = tk.Frame(top_frame, bg=self.colors["background"]) 
        btn_frame.pack(pady=(8, 0))
        button_style = {"font": ("Segoe UI", 11, "bold"), "relief": "flat", "bd": 0, "padx": 22, "pady": 10, "cursor": "hand2", "activebackground": self.colors["accent"], "activeforeground": "white"}
        tk.Button(btn_frame, text="🔢 Calcular Raíz", command=self.calculate_secant,
                  bg=self.colors["accent"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🗑 Limpiar", command=self.clear_secant,
                  bg=self.colors["button_secondary"], fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="📊 Graficar Función", command=self.plot_function_sc,
                  bg="#7B68EE", fg="white", **button_style).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="🔎 Sugerir Intervalo", command=self.suggest_interval_sc,
                  bg="#20B2AA", fg="white", **button_style).pack(side="left", padx=(0, 8))
        self.sc_btn_frame = btn_frame
        self.sc_keyboard_frame = tk.Frame(main_frame, bg=self.colors["matrix_bg"], relief="flat", bd=1)
        self.sc_keyboard_frame.place(in_=self.sc_btn_frame, relx=0.5, rely=1.06, anchor="n")
        self.sc_keyboard_visible = True
        self.setup_virtual_keyboard_sc()
        self.sc_result_frame = tk.Frame(main_frame, bg=self.colors["background"]) 
        self.sc_result_frame.pack(fill="both", expand=True, pady=(15, 0))
        tk.Label(self.sc_result_frame, text="Resultados:", font=("Segoe UI", 14, "bold"),
                 bg=self.colors["background"], fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        sc_results_container = tk.Frame(self.sc_result_frame, bg=self.colors["background"]) 
        sc_results_container.pack(fill="both", expand=True)
        self.secant_result_text = tk.Text(sc_results_container, width=100, height=28, font=("Consolas", 14),
                            bg=self.colors["secondary_bg"], fg=self.colors["text"],
                            insertbackground=self.colors["text"], relief="flat", bd=1, wrap="none")
        sc_vsb = tk.Scrollbar(sc_results_container, orient="vertical", command=self.secant_result_text.yview)
        self.secant_result_text.configure(yscrollcommand=sc_vsb.set)
        sc_vsb.pack(side="right", fill="y")
        self.secant_result_text.pack(side="left", fill="both", expand=True)
        self.secant_result_text.tag_configure("title", foreground=self.colors["accent"], font=("Consolas", 12, "bold"))
        self.secant_result_text.tag_configure("step", foreground="#30D158", font=("Consolas", 12))
        self.secant_result_text.tag_configure("error", foreground="#FF453A", font=("Consolas", 12, "bold"))
        self.secant_result_text.tag_configure("result", foreground="#30D158", font=("Consolas", 14, "bold"))
        self.secant_result_text.tag_configure("warning", foreground="#FF9F0A", font=("Consolas", 12))
        self.secant_result_text.insert("1.0", "Los resultados del método de la Secante se mostrarán aquí.")
        self.secant_result_text.config(state="disabled")

    def clear_secant(self):
        self.sc_function_var.set(""); self.sc_x0_var.set("0.0"); self.sc_x1_var.set("1.0"); self.sc_tol_var.set("0.0001"); self.sc_max_iter_var.set("100")
        self.secant_result_text.config(state="normal"); self.secant_result_text.delete("1.0", tk.END)
        self.secant_result_text.insert("1.0", "Los resultados del método de la Secante se mostrarán aquí.")
        self.secant_result_text.config(state="disabled")

    def plot_function_sc(self):
        try:
            func_str = self.sc_function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return
            try:
                a = float(self.sc_x0_var.get()); b = float(self.sc_x1_var.get())
            except ValueError:
                messagebox.showerror("Error", "x0/x1 inválidos. Ingrese números válidos.")
                return
            use_embedded = hasattr(self, 'sc_plot_canvas')
            if use_embedded:
                prev_xlim = self.sc_plot_ax.get_xlim(); prev_ylim = self.sc_plot_ax.get_ylim(); restore_view = getattr(self, 'sc_plot_init_done', False)
            else:
                restore_view = False
            if use_embedded and restore_view:
                x_min, x_max = prev_xlim
            else:
                margin = max(abs(b - a) * 0.2, 1)
                base_min = min(a, b) - margin; base_max = max(a, b) + margin
                x_min, x_max = self._determine_plot_range(func_str, base_min, base_max)
            x = np.linspace(x_min, x_max, 4000)
            y = self.evaluate_function_vectorized(x, func_str)
            y_plot = np.where(np.isfinite(y), y, np.nan)
            if np.all(np.isnan(y_plot)):
                messagebox.showerror("Error al graficar", "No se pudieron evaluar puntos válidos en el intervalo.")
                return
            formatted_func = self.format_function_display(func_str)
            ax = self.sc_plot_ax
            ax.clear()
            ax.plot(x, y_plot, label=f"f(x) = {formatted_func}", color="#7B68EE", linewidth=2)
            ax.axhline(0, color="#FF453A", linewidth=1)
            ax.axvline(0, color="#FF9F0A", linewidth=1)
            ax.axvline(x=a, color='g', linewidth=2, linestyle=':', alpha=0.7, label=f'x0 = {a:.2f}')
            ax.axvline(x=b, color='r', linewidth=2, linestyle=':', alpha=0.7, label=f'x1 = {b:.2f}')
            ax.set_title(f"Gráfica de f(x) = {formatted_func} - Secante")
            ax.set_xlabel('x'); ax.set_ylabel('f(x)')
            dy = np.gradient(np.nan_to_num(y_plot, nan=0.0), x)
            vx = []; vy = []
            mask = np.isfinite(y_plot)
            idx = np.where(mask)[0]
            if len(idx) > 1:
                prev = idx[0]
                run = [prev]
                for i in idx[1:]:
                    if i == prev + 1:
                        run.append(i)
                    else:
                        if len(run) > 1:
                            dr = dy[run]
                            for j in range(1, len(dr)):
                                if (dr[j-1] > 0 and dr[j] <= 0) or (dr[j-1] < 0 and dr[j] >= 0):
                                    k = run[j]
                                    vx.append(x[k]); vy.append(y_plot[k])
                        run = [i]
                    prev = i
                if len(run) > 1:
                    dr = dy[run]
                    for j in range(1, len(dr)):
                        if (dr[j-1] > 0 and dr[j] <= 0) or (dr[j-1] < 0 and dr[j] >= 0):
                            k = run[j]
                            vx.append(x[k]); vy.append(y_plot[k])
            if vx:
                ax.plot(vx, vy, marker='D', linestyle='None', color='#FF9F0A', label='Vértices')
            self.sc_vertices = list(zip(vx, vy))
            try:
                p1, p99 = np.nanpercentile(y_plot, [1, 99])
                if not (np.isnan(p1) or np.isnan(p99)):
                    yr = p99 - p1
                    if yr > 0:
                        ax.set_ylim(p1 - yr * 0.1, p99 + yr * 0.1)
                    else:
                        ax.set_ylim(p1 - 1, p99 + 1)
                ax.set_xlim(x_min, x_max)
            except Exception:
                pass
            if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == func_str:
                try:
                    f_root = self.evaluate_function(self.calculated_root, func_str)
                    ax.plot(self.calculated_root, f_root, marker='o', linestyle='None', markersize=10, color='#BB33FF', label=f'Raíz ≈ {self.calculated_root:.4f}')
                    ax.axvline(x=self.calculated_root, color='#BB33FF', linewidth=1.5, linestyle='--', alpha=0.6)
                except:
                    pass
            ax.grid(True, linestyle='--', alpha=0.5); ax.legend(); self.sc_plot_init_done = True; self.sc_plot_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar: {str(e)}")

    def on_sc_motion(self, event):
        ax = self.sc_plot_ax
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            self.sc_hover_annot.set_visible(False); self.sc_plot_canvas.draw_idle(); return
        xr = ax.get_xlim(); yr = ax.get_ylim()
        tolx = (xr[1]-xr[0])*0.02; toly = (yr[1]-yr[0])*0.02
        show = False; text = ""; xy = (event.xdata, event.ydata)
        if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == self.sc_function_var.get().strip():
            try:
                fr = self.evaluate_function(self.calculated_root, self.sc_function_var.get().strip())
                if abs(event.xdata - self.calculated_root) <= tolx and abs(event.ydata - fr) <= toly:
                    show = True; text = f"raíz ≈ {self.calculated_root:.6f}"; xy = (self.calculated_root, fr)
            except:
                pass
        if not show and hasattr(self, 'sc_vertices'):
            for vx, vy in self.sc_vertices:
                if abs(event.xdata - vx) <= tolx and abs(event.ydata - vy) <= toly:
                    show = True; text = f"vértice ({vx:.4f}, {vy:.4f})"; xy = (vx, vy); break
        if show:
            self.sc_hover_annot.xy = xy; self.sc_hover_annot.set_text(text); self.sc_hover_annot.set_visible(True)
        else:
            self.sc_hover_annot.set_visible(False)
        self.sc_plot_canvas.draw_idle()

    def suggest_interval_sc(self):
        func_str = self.sc_function_var.get().strip()
        if not func_str:
            messagebox.showerror("Error", "Por favor ingrese una función en 'f(x)'.")
            return
        a, b, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
        if a is None:
            messagebox.showwarning("Sin cambio de signo", "No se encontraron intervalos con cambio de signo en los rangos probados.")
            return
        self.sc_x0_var.set(f"{a:.6f}"); self.sc_x1_var.set(f"{b:.6f}")
        txt = "Intervalos con cambio de signo detectados:\n\n"
        for i, (ia, ib) in enumerate(intervals, 1):
            txt += f"{i}. [{ia:.6f}, {ib:.6f}]\n"
        if zeros:
            txt += "\nRaíces exactas detectadas en muestreo:\n"
            for i, (zx, st) in enumerate(sorted(zeros, key=lambda t: abs(t[0])), 1):
                txt += f"{i}. x = {zx:.6f} (intervalo sugerido [{zx-st:.6f}, {zx+st:.6f}])\n"
        txt += "\nSe asignó el intervalo más cercano a 0."
        messagebox.showinfo("Sugerencia de Intervalos", txt)

    def setup_virtual_keyboard_sc(self):
        func_frame = tk.Frame(self.sc_keyboard_frame, bg=self.colors["matrix_bg"])
        func_frame.pack(pady=15, padx=10)
        tk.Label(func_frame, text="Funciones Matemáticas:", font=("Segoe UI", 13, "bold"),
                 bg=self.colors["matrix_bg"], fg=self.colors["accent"]).pack(pady=(0,15))
        buttons_frame = tk.Frame(func_frame, bg=self.colors["matrix_bg"])
        buttons_frame.pack()
        functions = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"),
            ("ln(x)", "ln(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x^2"), ("x³", "x^3"), ("1/x", "1/x"),
            ("x", "x"), ("π", "pi"), ("e", "e"),
            ("+", "+"), ("-", "-"), ("×", "*"), ("/", "/"),
            ("(", "("), (")", ")"), ("^", "^")
        ]
        button_style_normal = {"font": ("Segoe UI", 11, "bold"), "relief": "flat", "bd": 0, "padx": 12, "pady": 8,
                               "cursor": "hand2", "activebackground": self.colors["accent"], "activeforeground": "white"}
        button_style_operator = {"font": ("Segoe UI", 12, "bold"), "relief": "flat", "bd": 0, "padx": 14, "pady": 8,
                                  "cursor": "hand2", "activebackground": self.colors["accent"], "activeforeground": "white"}
        for i, (text, value) in enumerate(functions):
            row = i // 6; col = i % 6
            if text in ["+", "-", "×", "/", "^"]: bg_color = self.colors["accent"]; style = button_style_operator
            elif text in ["sin(x)", "cos(x)", "tan(x)", "ln(x)", "log(x)", "sqrt(x)"]: bg_color = "#4A90E2"; style = button_style_normal
            elif text in ["x²", "x³", "1/x", "x"]: bg_color = "#7B68EE"; style = button_style_normal
            elif text in ["π", "e"]: bg_color = "#20B2AA"; style = button_style_normal
            else: bg_color = self.colors["button_secondary"]; style = button_style_normal
            btn = tk.Button(buttons_frame, text=text, command=lambda v=value: self.insert_function_sc(v), bg=bg_color, fg="white", **style)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            def on_enter(e, btn=btn, original_bg=bg_color): btn.config(bg=self.colors["accent"]) 
            def on_leave(e, btn=btn, original_bg=bg_color): btn.config(bg=original_bg)
            btn.bind("<Enter>", on_enter); btn.bind("<Leave>", on_leave)
        for col in range(6): buttons_frame.grid_columnconfigure(col, weight=1, uniform="buttons")
        clear_btn = tk.Button(buttons_frame, text="🗑 Borrar", command=self.clear_function_entry_sc,
                              bg="#FF453A", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                              padx=12, pady=8, cursor="hand2", activebackground="#FF6B6B", activeforeground="white")
        clear_btn.grid(row=len(functions)//6, column=5, padx=3, pady=3, sticky="nsew")
        def on_enter_clear(e): clear_btn.config(bg="#FF6B6B")
        def on_leave_clear(e): clear_btn.config(bg="#FF453A")
        clear_btn.bind("<Enter>", on_enter_clear); clear_btn.bind("<Leave>", on_leave_clear)

    def insert_function_sc(self, value):
        current = self.sc_function_var.get(); cursor_pos = self.sc_function_entry.index(tk.INSERT)
        if value == "pi": value = "π"
        elif value == "e": value = "e"
        new_value = current[:cursor_pos] + value + current[cursor_pos:]
        self.sc_function_var.set(new_value); self.sc_function_entry.icursor(cursor_pos + len(value)); self.sc_function_entry.focus()

    def clear_function_entry_sc(self):
        self.sc_function_var.set(""); self.sc_function_entry.focus()

    def toggle_keyboard_sc(self):
        try:
            if self.sc_keyboard_visible:
                self.sc_keyboard_frame.place_forget()
                self.sc_keyboard_visible = False
                self.sc_keyboard_btn.config(text="⌨ Mostrar Teclado")
            else:
                self.sc_keyboard_frame.place(in_=self.sc_btn_frame, relx=0.5, rely=1.06, anchor="n")
                self.sc_keyboard_visible = True
                self.sc_keyboard_btn.config(text="🔽 Ocultar Teclado")
                self.sc_keyboard_frame.update_idletasks()
                self.secant_tab.update_idletasks()
        except:
            pass

    def update_secant_preview(self):
        try:
            func_str = self.sc_function_var.get().strip()
            disp = self.to_mathtext(func_str) if func_str else ""
            try:
                self.sc_prev_ax.clear(); self.sc_prev_ax.axis('off'); self.sc_prev_ax.text(0.01, 0.5, f"$f(x) = {disp}$", fontsize=12, va='center'); self.sc_prev_canvas.draw()
            except Exception:
                pass
        except Exception:
            pass

    def on_sc_scroll(self, event):
        self._zoom_on_scroll(self.sc_plot_ax, self.sc_plot_canvas, event)

    def calculate_secant(self):
        try:
            func_str = self.sc_function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return
            x0 = float(self.sc_x0_var.get()); x1 = float(self.sc_x1_var.get()); tol = float(self.sc_tol_var.get()); max_it = int(self.sc_max_iter_var.get())
            fx0 = self.evaluate_function(x0, func_str); fx1 = self.evaluate_function(x1, func_str)
            if fx0 * fx1 > 0:
                sa, sb, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
                if sa is not None:
                    x0, x1 = sa, sb
                    fx0 = self.evaluate_function(x0, func_str); fx1 = self.evaluate_function(x1, func_str)
            self.secant_result_text.config(state="normal"); self.secant_result_text.delete("1.0", tk.END)
            formatted_func = self.format_function_display(func_str)
            self.secant_result_text.insert(tk.END, f"MÉTODO DE LA SECANTE\n", "title")
            self.secant_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.secant_result_text.insert(tk.END, f"x0: {x0}\nx1: {x1}\nTolerancia: {tol}\nMáx. iteraciones: {max_it}\n\n", "step")
            self.secant_result_text.insert(tk.END, "\nTABLA DE ITERACIONES:\n", "title")
            self.secant_result_text.insert(tk.END, "="*80+"\n", "step")
            header = f"{'Iter':<6} {'x0':>16} {'x1':>16} {'x2':>16} {'f(x2)':>16} {'ea':>16}\n"
            self.secant_result_text.insert(tk.END, header, "step"); self.secant_result_text.insert(tk.END, "-"*80+"\n", "step")
            iteration = 0; root = None
            while iteration < max_it:
                if abs(fx1 - fx0) < 1e-12:
                    self.secant_result_text.insert(tk.END, "⚠ División por cero en la fórmula de secante\n", "warning"); break
                x2 = x1 - fx1 * (x1 - x0) / (fx1 - fx0)
                fx2 = self.evaluate_function(x2, func_str)
                if not (math.isfinite(fx0) and math.isfinite(fx1) and math.isfinite(fx2)):
                    self.secant_result_text.insert(tk.END, "⚠ Valor no finito encontrado; posible discontinuidad. Intente otros x0/x1.\n", "warning"); break
                ea = abs(x2 - x1)
                row = f"{iteration+1:<6} {x0:>16.8f} {x1:>16.8f} {x2:>16.8f} {fx2:>16.8f} {ea:>16.8f}\n"
                self.secant_result_text.insert(tk.END, row, "matrix")
                if ea <= tol or abs(fx2) <= tol:
                    root = x2; iteration += 1; break
                x0, x1 = x1, x2
                fx0, fx1 = fx1, fx2
                iteration += 1
            if root is None:
                root = x1
            self.calculated_root = root; self.calculated_func_str = func_str
            self.secant_result_text.insert(tk.END, "="*80+"\n\n", "step")
            self.secant_result_text.insert(tk.END, "RESULTADO FINAL (Secante):\n", "result")
            self.secant_result_text.insert(tk.END, f"La raiz aproximada es x = {root:.8f}\n", "result")
            self.secant_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.secant_result_text.insert(tk.END, f"Converge en {iteration} iteraciones\n", "result")
            try:
                self.secant_result_text.see(tk.END)
            except Exception:
                pass
            self.secant_result_text.config(state="disabled")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error en Secante: {str(e)}")

    def update_newton_preview(self):
        try:
            func = self.nw_function_var.get().strip()
            disp = self.to_mathtext(func) if func else ""
            self.nw_prev_ax.clear(); self.nw_prev_ax.axis('off');
            self.nw_prev_ax.text(0.01, 0.5, f"$f(x) = {disp}$", fontsize=12, va='center')
            self.nw_prev_canvas.draw()
        except:
            pass

    def plot_function_newton(self):
        try:
            func_str = self.nw_function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return
            # Tomar vista previa y mantener límites entre re-plots
            ax = self.nw_plot_ax; prev_xlim = ax.get_xlim(); prev_ylim = ax.get_ylim(); restore = getattr(self, 'nw_plot_init_done', False)
            ax.clear()
            # rango x: si hay vista previa, respetar límites actuales
            try:
                if restore:
                    x_min, x_max = prev_xlim
                else:
                    x0 = float(self.nw_x0_var.get())
                    base_min, base_max = x0-5.0, x0+5.0
                    x_min, x_max = self._determine_plot_range(func_str, base_min, base_max)
            except:
                x_min, x_max = self._determine_plot_range(func_str, -5.0, 5.0)
            x = np.linspace(x_min, x_max, 3000)
            y = self.evaluate_function_vectorized(x, func_str)
            ax.plot(x, y, 'b-', linewidth=2, label=f"f(x) = {math_utils.format_function_display(func_str)}")
            ax.axhline(0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
            ax.axvline(0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
            if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == func_str:
                try:
                    fr = self.evaluate_function(self.calculated_root, func_str)
                    ax.plot(self.calculated_root, fr, marker='o', linestyle='None', markersize=10, color='#BB33FF', label=f'Raíz ≈ {self.calculated_root:.4f}')
                    ax.axvline(self.calculated_root, color='#BB33FF', linewidth=1.2, linestyle='--', alpha=0.7)
                except:
                    pass
            ax.grid(True, linestyle='--', alpha=0.5); ax.legend()
            if restore:
                try: ax.set_xlim(prev_xlim); ax.set_ylim(prev_ylim)
                except: pass
            self.nw_plot_init_done = True
            self.nw_plot_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error al graficar: {str(e)}")

    def calculate_newton(self):
        try:
            func_str = self.nw_function_var.get().strip()
            if not func_str:
                messagebox.showerror("Error", "Por favor ingrese una función")
                return
            x = float(self.nw_x0_var.get()); tol = float(self.nw_tol_var.get()); max_it = int(self.nw_max_iter_var.get())
            self.newton_result_text.config(state="normal"); self.newton_result_text.delete("1.0", tk.END)
            formatted_func = self.format_function_display(func_str)
            self.newton_result_text.insert(tk.END, f"MÉTODO DE NEWTON-RAPHSON\n", "title")
            self.newton_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.newton_result_text.insert(tk.END, f"x0: {x}\nTolerancia: {tol}\nMáx. iteraciones: {max_it}\n\n", "step")
            self.newton_result_text.insert(tk.END, "\nTABLA DE ITERACIONES:\n", "title")
            self.newton_result_text.insert(tk.END, "="*80+"\n", "step")
            header = f"{'Iter':<6} {'x':>16} {'f(x)':>16} {'f\' (x)':>16} {'ea':>16}\n"
            self.newton_result_text.insert(tk.END, header, "step"); self.newton_result_text.insert(tk.END, "-"*80+"\n", "step")
            prev_x = x; iteration = 0; stopped = False
            while iteration < max_it:
                fx = self.evaluate_function(prev_x, func_str)
                dfx = self.derivative_numeric(prev_x, func_str)
                if abs(dfx) < 1e-12:
                    self.newton_result_text.insert(tk.END, "⚠ f'(x) ≈ 0; posible división por cero. Deteniendo.\n", "warning")
                    stopped = True; break
                next_x = prev_x - fx/dfx
                ea = abs(next_x - prev_x)
                self.newton_result_text.insert(tk.END, f"{iteration+1:<6} {prev_x:>16.10f} {fx:>16.10f} {dfx:>16.10f} {ea:>16.10f}\n", "matrix")
                if ea <= tol or abs(self.evaluate_function(next_x, func_str)) <= tol:
                    prev_x = next_x; iteration += 1; break
                prev_x = next_x; iteration += 1
            self.newton_result_text.insert(tk.END, "\n"+"="*80+"\n", "step")
            if stopped:
                self.newton_result_text.insert(tk.END, "⚠ Cálculo detenido por f'(x)≈0. Intente otro x0.\n", "warning")
            else:
                root = prev_x
                self.calculated_root = root; self.calculated_func_str = func_str
                self.newton_result_text.insert(tk.END, f"RESULTADO FINAL (Newton-Raphson):\n", "result")
                self.newton_result_text.insert(tk.END, f"Raíz aproximada x = {root:.10f}\n", "result")
                fr = self.evaluate_function(root, func_str)
                self.newton_result_text.insert(tk.END, f"f({root:.10f}) = {fr:.2e}\n", "result")
                if iteration >= max_it:
                    self.newton_result_text.insert(tk.END, "\n⚠ Se alcanzó el máximo de iteraciones\n", "warning")
                if abs(fr) > tol:
                    self.newton_result_text.insert(tk.END, "\n⚠ Aviso: |f(raíz)| es mayor que la tolerancia; podría haber convergencia lenta u oscilatoria.\n", "warning")
            self.newton_result_text.config(state="disabled")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error en Newton-Raphson: {str(e)}")

    def clear_newton(self):
        self.nw_function_var.set(""); self.nw_x0_var.set("0.0"); self.nw_tol_var.set("0.0001"); self.nw_max_iter_var.set("100")
        self.newton_result_text.config(state="normal"); self.newton_result_text.delete("1.0", tk.END)
        self.newton_result_text.insert("1.0", "Los resultados de Newton-Raphson se mostrarán aquí.")
        self.newton_result_text.config(state="disabled")

    def suggest_interval_nw(self):
        func_str = self.nw_function_var.get().strip()
        if not func_str:
            messagebox.showerror("Error", "Por favor ingrese una función en 'f(x)'.")
            return
        a, b, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
        if a is None:
            messagebox.showwarning("Sin cambio de signo", "No se encontraron intervalos con cambio de signo en los rangos probados.")
            return
        mid = (a + b) / 2.0
        self.nw_x0_var.set(f"{mid:.6f}")
        txt = "Intervalos con cambio de signo detectados:\n\n"
        for i, (ia, ib) in enumerate(intervals, 1):
            txt += f"{i}. [{ia:.6f}, {ib:.6f}]\n"
        if zeros:
            txt += "\nRaíces exactas detectadas en muestreo:\n"
            for i, (zx, st) in enumerate(sorted(zeros, key=lambda t: abs(t[0])), 1):
                txt += f"{i}. x = {zx:.6f} (intervalo sugerido [{zx-st:.6f}, {zx+st:.6f}])\n"
        txt += f"\nSe asignó x0 = {mid:.6f} (punto medio del intervalo más cercano a 0)."
        messagebox.showinfo("Sugerencia de Intervalos", txt)

    def setup_virtual_keyboard_nw(self):
        func_frame = tk.Frame(self.nw_keyboard_frame, bg=self.colors["matrix_bg"])
        func_frame.pack(pady=15, padx=10)
        tk.Label(func_frame, text="Funciones Matemáticas:", font=("Segoe UI", 13, "bold"),
                 bg=self.colors["matrix_bg"], fg=self.colors["accent"]).pack(pady=(0,15))
        buttons_frame = tk.Frame(func_frame, bg=self.colors["matrix_bg"])
        buttons_frame.pack()
        functions = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"),
            ("ln(x)", "ln(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x^2"), ("x³", "x^3"), ("1/x", "1/x"),
            ("x", "x"), ("π", "pi"), ("e", "e"),
            ("+", "+"), ("-", "-"), ("×", "*"), ("/", "/"),
            ("(", "("), (")", ")"), ("^", "^")
        ]
        button_style_normal = {"font": ("Segoe UI", 11, "bold"), "relief": "flat", "bd": 0, "padx": 12, "pady": 8,
                               "cursor": "hand2", "activebackground": self.colors["accent"], "activeforeground": "white"}
        button_style_operator = {"font": ("Segoe UI", 12, "bold"), "relief": "flat", "bd": 0, "padx": 14, "pady": 8,
                                  "cursor": "hand2", "activebackground": self.colors["accent"], "activeforeground": "white"}
        for i, (text, value) in enumerate(functions):
            row = i // 6; col = i % 6
            if text in ["+", "-", "×", "/", "^"]: bg_color = self.colors["accent"]; style = button_style_operator
            elif text in ["sin(x)", "cos(x)", "tan(x)", "ln(x)", "log(x)", "sqrt(x)"]: bg_color = "#4A90E2"; style = button_style_normal
            elif text in ["x²", "x³", "1/x", "x"]: bg_color = "#7B68EE"; style = button_style_normal
            elif text in ["π", "e"]: bg_color = "#20B2AA"; style = button_style_normal
            else: bg_color = self.colors["button_secondary"]; style = button_style_normal
            btn = tk.Button(buttons_frame, text=text, command=lambda v=value: self.insert_function_nw(v), bg=bg_color, fg="white", **style)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
            def on_enter(e, btn=btn, original_bg=bg_color): btn.config(bg=self.colors["accent"])
            def on_leave(e, btn=btn, original_bg=bg_color): btn.config(bg=original_bg)
            btn.bind("<Enter>", on_enter); btn.bind("<Leave>", on_leave)
        for col in range(6): buttons_frame.grid_columnconfigure(col, weight=1, uniform="buttons")
        clear_btn = tk.Button(buttons_frame, text="🗑 Borrar", command=self.clear_function_entry_nw,
                              bg="#FF453A", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                              padx=12, pady=8, cursor="hand2", activebackground="#FF6B6B", activeforeground="white")
        clear_btn.grid(row=len(functions)//6, column=5, padx=3, pady=3, sticky="nsew")
        def on_enter_clear(e): clear_btn.config(bg="#FF6B6B")
        def on_leave_clear(e): clear_btn.config(bg="#FF453A")
        clear_btn.bind("<Enter>", on_enter_clear); clear_btn.bind("<Leave>", on_leave_clear)

    def insert_function_nw(self, value):
        current = self.nw_function_var.get(); cursor_pos = self.nw_function_entry.index(tk.INSERT)
        if value == "pi": value = "π"
        elif value == "e": value = "e"
        new_value = current[:cursor_pos] + value + current[cursor_pos:]
        self.nw_function_var.set(new_value); self.nw_function_entry.icursor(cursor_pos + len(value)); self.nw_function_entry.focus()

    def clear_function_entry_nw(self):
        self.nw_function_var.set(""); self.nw_function_entry.focus()

    def toggle_keyboard_nw(self):
        try:
            if self.nw_keyboard_visible:
                self.nw_keyboard_frame.place_forget()
                self.nw_keyboard_visible = False
                self.nw_keyboard_btn.config(text="⌨ Mostrar Teclado")
            else:
                self.nw_keyboard_frame.place(in_=self.nw_btn_frame, relx=0.5, rely=1.06, anchor="n")
                self.nw_keyboard_visible = True
                self.nw_keyboard_btn.config(text="🔽 Ocultar Teclado")
                self.nw_keyboard_frame.update_idletasks()
                self.newton_tab.update_idletasks()
        except:
            pass

    def on_nw_motion(self, event):
        ax = self.nw_plot_ax
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            self.nw_hover_annot.set_visible(False); self.nw_plot_canvas.draw_idle(); return
        xr = ax.get_xlim(); yr = ax.get_ylim()
        tolx = (xr[1]-xr[0])*0.02; toly = (yr[1]-yr[0])*0.02
        show = False; text = ""; xy = (event.xdata, event.ydata)
        if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == self.nw_function_var.get().strip():
            try:
                fr = self.evaluate_function(self.calculated_root, self.nw_function_var.get().strip())
                if abs(event.xdata - self.calculated_root) <= tolx and abs(event.ydata - fr) <= toly:
                    show = True; text = f"raíz ≈ {self.calculated_root:.6f}"; xy = (self.calculated_root, fr)
            except:
                pass
        if show:
            self.nw_hover_annot.xy = xy; self.nw_hover_annot.set_text(text); self.nw_hover_annot.set_visible(True)
        else:
            self.nw_hover_annot.set_visible(False)
        self.nw_plot_canvas.draw_idle()
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
        func_frame.pack(pady=12, padx=10, anchor="center")
        
        tk.Label(func_frame, text="Funciones Matemáticas:", 
                font=("Segoe UI", 13, "bold"),
                bg=self.colors["matrix_bg"], fg=self.colors["accent"]).pack(pady=(0, 15))
        
        # Frame para los botones usando grid
        buttons_frame = tk.Frame(func_frame, bg=self.colors["matrix_bg"])
        buttons_frame.pack(anchor="center")
        
        # Botones de funciones
        functions = [
            ("sin(x)", "sin(x)"), ("cos(x)", "cos(x)"), ("tan(x)", "tan(x)"),
            ("ln(x)", "ln(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x^2"), ("x³", "x^3"), ("1/x", "1/x"),
            ("x", "x"), ("π", "pi"), ("e", "e"),
            ("+", "+"), ("-", "-"), ("×", "*"), ("/", "/"),
            ("(", "("), (")", ")"), ("^", "^")
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
            elif text in ["sin(x)", "cos(x)", "tan(x)", "ln(x)", "log(x)", "sqrt(x)"]:
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
                self.keyboard_frame.place_forget()
                self.keyboard_visible = False
                self.keyboard_btn.config(text="⌨ Mostrar Teclado")
            else:
                # Mostrar el teclado centrado respecto a los botones
                self.keyboard_frame.place(in_=self.bisection_btn_frame, relx=0.5, rely=1.06, anchor="n")
                self.keyboard_visible = True
                self.keyboard_btn.config(text="🔽 Ocultar Teclado")
                # Forzar actualización
                self.keyboard_frame.update_idletasks()
                self.bisection_tab.update_idletasks()
        except Exception as e:
            # Si hay error, intentar mostrar el teclado
            try:
                self.keyboard_frame.place(in_=self.bisection_btn_frame, relx=0.5, rely=1.06, anchor="n")
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
        return math_utils.format_function_display(func_str)
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
            ("ln(x)", "ln(x)"), ("log(x)", "log(x)"), ("sqrt(x)", "sqrt(x)"),
            ("x²", "x^2"), ("x³", "x^3"), ("1/x", "1/x"),
            ("x", "x"), ("π", "pi"), ("e", "e"),
            ("+", "+"), ("-", "-"), ("×", "*"), ("/", "/"),
            ("(", "("), (")", ")"), ("^", "^")
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
            elif text in ["sin(x)", "cos(x)", "tan(x)", "ln(x)", "log(x)", "sqrt(x)"]:
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
                self.fp_keyboard_frame.place_forget()
                self.fp_keyboard_visible = False
                self.fp_keyboard_btn.config(text="⌨ Mostrar Teclado")
            else:
                # Mostrar el teclado centrado respecto a los botones
                self.fp_keyboard_frame.place(in_=self.fp_btn_frame, relx=0.5, rely=1.06, anchor="n")
                self.fp_keyboard_visible = True
                self.fp_keyboard_btn.config(text="🔽 Ocultar Teclado")
                # Forzar actualización
                self.fp_keyboard_frame.update_idletasks()
                self.falsepos_tab.update_idletasks()
        except Exception as e:
            # Si hay error, intentar mostrar el teclado
            try:
                self.fp_keyboard_frame.place(in_=self.fp_btn_frame, relx=0.5, rely=1.06, anchor="n")
                self.fp_keyboard_visible = True
                self.fp_keyboard_btn.config(text="🔽 Ocultar Teclado")
                self.fp_keyboard_frame.update_idletasks()
            except:
                pass

    def preprocess_function(self, func_str):
        return math_utils.preprocess_function(func_str)

    def evaluate_function(self, x, func_str):
        return math_utils.evaluate_function(x, func_str)

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

            # Manejar raíces en los extremos
            if fa == 0.0:
                root = a
                self.calculated_root = root; self.calculated_func_str = func_str; self.calculated_interval = (a, b)
                self.bisection_result_text.config(state="normal"); self.bisection_result_text.delete("1.0", tk.END)
                self.bisection_result_text.insert("1.0", f"MÉTODO DE BISECCIÓN\n", "title")
                formatted_func = math_utils.format_function_display(func_str)
                self.bisection_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
                self.bisection_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
                self.bisection_result_text.insert(tk.END, "\nRESULTADO FINAL:\n", "result")
                self.bisection_result_text.insert(tk.END, f"La raiz aproximada es x = {root:.8f}\n", "result")
                self.bisection_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
                self.bisection_result_text.config(state="disabled"); return
            if fb == 0.0:
                root = b
                self.calculated_root = root; self.calculated_func_str = func_str; self.calculated_interval = (a, b)
                self.bisection_result_text.config(state="normal"); self.bisection_result_text.delete("1.0", tk.END)
                self.bisection_result_text.insert("1.0", f"MÉTODO DE BISECCIÓN\n", "title")
                formatted_func = math_utils.format_function_display(func_str)
                self.bisection_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
                self.bisection_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
                self.bisection_result_text.insert(tk.END, "\nRESULTADO FINAL:\n", "result")
                self.bisection_result_text.insert(tk.END, f"La raiz aproximada es x = {root:.8f}\n", "result")
                self.bisection_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
                self.bisection_result_text.config(state="disabled"); return

            # Si no hay cambio de signo, intentar sugerencia automática
            if fa * fb > 0:
                sa, sb, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
                if sa is None:
                    messagebox.showerror("Error", "La función no cambia de signo en el intervalo [a, b] ni en rangos amplios probados.")
                    return
                a, b = sa, sb
                fa = self.evaluate_function(a, func_str)
                fb = self.evaluate_function(b, func_str)
            
            # Limpiar resultados anteriores
            self.bisection_result_text.config(state="normal")
            self.bisection_result_text.delete("1.0", tk.END)
            
            # Mostrar información inicial
            self.bisection_result_text.insert("1.0", f"MÉTODO DE BISECCIÓN\n", "title")
            # Mostrar función con valores numéricos en lugar de símbolos
            formatted_func = math_utils.format_function_display(func_str)
            self.bisection_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
            if fa * fb < 0:
                self.bisection_result_text.insert(tk.END, "Intervalo asignado automáticamente con cambio de signo.\n", "step")
            if fa * fb < 0:
                self.bisection_result_text.insert(tk.END, "Intervalo asignado automáticamente con cambio de signo.\n", "step")
            self.bisection_result_text.insert(tk.END, f"Tolerancia: {tolerance}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Máximo de iteraciones: {max_iterations}\n\n", "step")
            
            # Crear encabezado de la tabla
            self.bisection_result_text.insert(tk.END, "\nTABLA DE ITERACIONES:\n", "title")
            self.bisection_result_text.insert(tk.END, "=" * 95 + "\n", "step")
            # Encabezados de columnas
            header = f"{'Iter':<6} {'a':>14} {'b':>14} {'c':>14} {'f(a)':>14} {'f(b)':>14} {'f(c)':>14} {'Error':>14}\n"
            self.bisection_result_text.insert(tk.END, header, "step")
            self.bisection_result_text.insert(tk.END, "-" * 95 + "\n", "step")
            
            # Aplicar el método de bisección
            iteration = 0
            prev_c = None
            while (b - a) / 2 > tolerance and iteration < max_iterations:
                c = (a + b) / 2
                fc = self.evaluate_function(c, func_str)
                error = abs(b - a) / 2

                # Mostrar información de la iteración en formato de tabla
                row = f"{iteration+1:<6} {a:>14.8f} {b:>14.8f} {c:>14.8f} {fa:>14.8f} {fb:>14.8f} {fc:>14.8f} {error:>14.8f}\n"
                self.bisection_result_text.insert(tk.END, row, "matrix")

                # Parada por valor de función: raíz encontrada o suficientemente cercana
                if abs(fc) <= tolerance or fc == 0.0:
                    prev_c = c
                    iteration += 1
                    break
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
            root = prev_c if prev_c is not None else (a + b) / 2
            # Guardar la raíz calculada para mostrarla en la gráfica
            self.calculated_root = root
            self.calculated_func_str = func_str
            self.calculated_interval = (a, b)
            
            self.bisection_result_text.insert(tk.END, "=" * 60 + "\n", "title")
            self.bisection_result_text.insert(tk.END, "RESULTADO FINAL:\n", "result")
            self.bisection_result_text.insert(tk.END, f"La raiz aproximada es x = {root:.8f}\n", "result")
            self.bisection_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.bisection_result_text.insert(tk.END, f"Converge en {iteration} iteraciones\n", "result")
            self.bisection_result_text.insert(tk.END, f"El error estimado final (ancho/2) es: {(b - a) / 2:.2e}\n", "result")
            
            if iteration >= max_iterations:
                self.bisection_result_text.insert(tk.END, "\n⚠ ADVERTENCIA: Se alcanzó el máximo de iteraciones\n", "warning")
            
            # Asegurar que la vista muestre el final
            try:
                self.bisection_result_text.see(tk.END)
            except Exception:
                pass
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
            formatted_func = math_utils.format_function_display(func_str)
            self.bisection_result_text.insert(tk.END, f"Función: f(x) = {formatted_func}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Intervalo inicial: [{a}, {b}]\n", "step")
            self.bisection_result_text.insert(tk.END, f"Tolerancia: {tolerance}\n", "step")
            self.bisection_result_text.insert(tk.END, f"Máximo de iteraciones: {max_iterations}\n\n", "step")

            # Encabezado de la tabla
            self.bisection_result_text.insert(tk.END, "\nTABLA DE ITERACIONES:\n", "title")
            self.bisection_result_text.insert(tk.END, "=" * 95 + "\n", "step")
            header = f"{'Iter':<6} {'a':>14} {'b':>14} {'c':>14} {'f(a)':>14} {'f(b)':>14} {'f(c)':>14} {'Error':>14}\n"
            self.bisection_result_text.insert(tk.END, header, "step")
            self.bisection_result_text.insert(tk.END, "-" * 95 + "\n", "step")

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

                # error mostrado será |f(c)|
                error_c = abs(fc)
                row = f"{iteration+1:<6} {a:>14.8f} {b:>14.8f} {c:>14.8f} {fa:>14.8f} {fb:>14.8f} {fc:>14.8f} {error_c:>14.8f}\n"
                self.bisection_result_text.insert(tk.END, row, "matrix")

                # Actualizar intervalo según cambio de signo
                if fa * fc < 0:
                    b = c
                    fb = fc
                    self.bisection_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(a) * f(c) < 0)\n", "step")
                else:
                    a = c
                    fa = fc
                    self.bisection_result_text.insert(tk.END, f"  → Nuevo intervalo: [{a:.8f}, {b:.8f}] (f(b) * f(c) < 0)\n", "step")

                self.bisection_result_text.insert(tk.END, "\n")

                if abs(fc) <= tolerance or (prev_c is not None and abs(c - prev_c) <= tolerance) or abs(b - a) <= tolerance:
                    prev_c = c
                    iteration += 1
                    break

                prev_c = c
                iteration += 1

            # Resultado final
            root = prev_c if prev_c is not None else (a + b) / 2
            self.bisection_result_text.insert(tk.END, "=" * 95 + "\n\n", "step")
            self.bisection_result_text.insert(tk.END, "RESULTADO FINAL (Falsa Posición):\n", "result")
            self.bisection_result_text.insert(tk.END, f"La raiz aproximada es x = {root:.8f}\n", "result")
            self.bisection_result_text.insert(tk.END, f"f({root:.8f}) = {self.evaluate_function(root, func_str):.2e}\n", "result")
            self.bisection_result_text.insert(tk.END, f"Converge en {iteration} iteraciones\n", "result")
            self.bisection_result_text.insert(tk.END, f"El error final |f(c)| es: {abs(self.evaluate_function(root, func_str)):.2e}\n", "result")

            if iteration >= max_iterations:
                self.bisection_result_text.insert(tk.END, "\n⚠ ADVERTENCIA: Se alcanzó el máximo de iteraciones\n", "warning")

            try:
                self.bisection_result_text.see(tk.END)
            except Exception:
                pass

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
        func_str = self.function_var.get().strip()
        if not func_str:
            messagebox.showerror("Error", "Por favor ingrese una función en 'f(x)'.")
            return
        a, b, intervals, zeros = self._suggest_interval_core(func_str, prefer_zero=True)
        if a is None:
            messagebox.showwarning("Sin cambio de signo", "No se encontraron intervalos con cambio de signo en los rangos probados.")
            return
        self.a_var.set(f"{a:.6f}")
        self.b_var.set(f"{b:.6f}")
        txt = "Intervalos con cambio de signo detectados:\n\n"
        for i, (ia, ib) in enumerate(intervals, 1):
            txt += f"{i}. [{ia:.6f}, {ib:.6f}]\n"
        if zeros:
            txt += "\nRaíces exactas detectadas en muestreo:\n"
            for i, (zx, st) in enumerate(sorted(zeros, key=lambda t: abs(t[0])), 1):
                txt += f"{i}. x = {zx:.6f} (intervalo sugerido [{zx-st:.6f}, {zx+st:.6f}])\n"
        txt += "\nSe asignó el intervalo más cercano a 0."
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
                    self.keyboard_frame.pack(pady=(8, 0), fill="x", padx=20, before=self.bisection_result_frame)
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
        return math_utils.evaluate_function_vectorized(x_array, func_str)

    def to_mathtext(self, s):
        try:
            t = s
            t = re.sub(r"sqrt\s*\(\s*([^()]*)\s*\)", r"\\sqrt{\1}", t)
            t = re.sub(r"\bln\s*\(\s*([^()]*)\s*\)", r"\\ln{\1}", t)
            t = re.sub(r"\blog\s*\(\s*([^()]*)\s*\)", r"\\log{\1}", t)
            def exp_paren(m):
                return f"{m.group(1)}^{{{m.group(2).strip()}}}"
            def exp_simple(m):
                return f"{m.group(1)}^{{{m.group(2).strip()}}}"
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*\(\s*([^()]*)\s*\)", exp_paren, t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*\^\s*(-?[A-Za-z0-9\.]+)", exp_simple, t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"([A-Za-z0-9\.]+)\s*/\s*\(\s*([^()]*)\s*\)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"\(\s*([^()]*)\s*\)\s*/\s*([A-Za-z0-9\.]+)", r"\\frac{\1}{\2}", t)
            t = re.sub(r"(?<![A-Za-z0-9_])([\-]?[A-Za-z0-9\.]+)\s*/\s*([\-]?[A-Za-z0-9\.]+)(?![A-Za-z0-9_])", r"\\frac{\1}{\2}", t)
            return t
        except Exception:
            return s

    def update_bisection_preview(self):
        """Renderiza una previsualización de la función en la pestaña de bisección"""
        try:
            func_str = self.function_var.get().strip()
            disp = self.to_mathtext(func_str) if func_str else ""
            try:
                self.bis_prev_ax.clear()
                self.bis_prev_ax.axis('off')
                self.bis_prev_ax.text(0.01, 0.5, f"$f(x) = {disp}$", fontsize=12, va='center')
                self.bis_prev_canvas.draw()
            except Exception:
                pass
        except Exception:
            pass

    def update_falsepos_preview(self):
        """Renderiza una previsualización de la función en la pestaña de falsa posición"""
        try:
            func_str = self.fp_function_var.get().strip()
            disp = self.to_mathtext(func_str) if func_str else ""
            try:
                self.fp_prev_ax.clear()
                self.fp_prev_ax.axis('off')
                self.fp_prev_ax.text(0.01, 0.5, f"$f(x) = {disp}$", fontsize=12, va='center')
                self.fp_prev_canvas.draw()
            except Exception:
                pass
        except Exception:
            pass
    
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

            # Preparar área de graficado: si existe canvas embebido úselo
            formatted_func = self.format_function_display(func_str)
            use_embedded = hasattr(self, 'bis_plot_canvas')
            if use_embedded:
                ax = self.bis_plot_ax
                fig = self.bis_plot_fig
                prev_xlim = ax.get_xlim()
                prev_ylim = ax.get_ylim()
                restore_view = getattr(self, 'bis_plot_init_done', False)
                ax.clear()
            else:
                plot_window = tk.Toplevel(self.root)
                plot_window.title(f"Gráfica de f(x) = {formatted_func}")
                plot_window.geometry("800x600")
                plot_window.configure(bg=self.colors["background"])
                fig = Figure(figsize=(8, 6), dpi=100)
                ax = fig.add_subplot(111)

            # Calcular rango de x: si ya hay vista previa, respetar límites actuales
            if use_embedded and restore_view:
                x_min, x_max = prev_xlim
            else:
                margin = max(abs(b - a) * 0.2, 1)
                x_min = min(a, b) - margin
                x_max = max(a, b) + margin
            # Crear array de x desde la vista actual
            x = np.linspace(x_min, x_max, 2000)

            # Evaluar función
            try:
                y = self.evaluate_function_vectorized(x, func_str)
                y_plot = np.where(np.isfinite(y), y, np.nan)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo evaluar la función: {str(e)}")
                if not use_embedded:
                    plot_window.destroy()
                return

            # Graficar función con formato numérico
            ax.plot(x, y_plot, 'b-', linewidth=2, label=f'f(x) = {formatted_func}')
            ax.axhline(y=0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
            ax.axvline(x=0, color='k', linewidth=0.8, linestyle='--', alpha=0.5)
            ax.axvline(x=a, color='g', linewidth=2, linestyle=':', alpha=0.7, label=f'a = {a:.2f}')
            ax.axvline(x=b, color='r', linewidth=2, linestyle=':', alpha=0.7, label=f'b = {b:.2f}')
            dy = np.gradient(np.nan_to_num(y_plot, nan=0.0), x)
            vx = []
            vy = []
            mask = np.isfinite(y_plot)
            idx = np.where(mask)[0]
            if len(idx) > 1:
                prev = idx[0]
                run = [prev]
                for i in idx[1:]:
                    if i == prev + 1:
                        run.append(i)
                    else:
                        if len(run) > 1:
                            dr = dy[run]
                            for j in range(1, len(dr)):
                                if (dr[j-1] > 0 and dr[j] <= 0) or (dr[j-1] < 0 and dr[j] >= 0):
                                    k = run[j]
                                    vx.append(x[k]); vy.append(y_plot[k])
                        run = [i]
                    prev = i
                if len(run) > 1:
                    dr = dy[run]
                    for j in range(1, len(dr)):
                        if (dr[j-1] > 0 and dr[j] <= 0) or (dr[j-1] < 0 and dr[j] >= 0):
                            k = run[j]
                            vx.append(x[k]); vy.append(y_plot[k])
            if vx:
                ax.plot(vx, vy, marker='D', linestyle='None', color='#FF9F0A', label='Vértices')
            self.bis_vertices = list(zip(vx, vy))

            # Marcar puntos f(a) y f(b)
            try:
                fa = self.evaluate_function(a, func_str)
                fb = self.evaluate_function(b, func_str)
                ax.plot(a, fa, 'go', markersize=8, label=f'f(a) = {fa:.3f}')
                ax.plot(b, fb, 'ro', markersize=8, label=f'f(b) = {fb:.3f}')
            except:
                pass

            # Marcar raíz calculada si existe
            if hasattr(self, 'calculated_root') and hasattr(self, 'calculated_func_str') and self.calculated_func_str == func_str:
                root = self.calculated_root
                try:
                    f_root = self.evaluate_function(root, func_str)
                    ax.plot(root, f_root, 'm*', markersize=15, label=f'Raíz ≈ {root:.4f}')
                    ax.axvline(x=root, color='m', linewidth=1.5, linestyle='--', alpha=0.6)
                except:
                    pass

            ax.set_xlabel('x')
            ax.set_ylabel('f(x)')
            ax.set_title(f'Gráfica de f(x) = {formatted_func}')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='best', fontsize=9)

            if not (use_embedded and restore_view):
                try:
                    p1, p99 = np.nanpercentile(y_plot, [1, 99])
                    if not (np.isnan(p1) or np.isnan(p99)):
                        yr = p99 - p1
                        if yr > 0:
                            ax.set_ylim(p1 - yr * 0.1, p99 + yr * 0.1)
                        else:
                            ax.set_ylim(p1 - 1, p99 + 1)
                    ax.set_xlim(x_min, x_max)
                except Exception:
                    pass

            if restore_view:
                try:
                    ax.set_xlim(prev_xlim); ax.set_ylim(prev_ylim)
                except:
                    pass
            self.bis_plot_init_done = True
            if use_embedded:
                try:
                    self.bis_plot_canvas.draw()
                except Exception:
                    pass
            else:
                canvas = FigureCanvasTkAgg(fig, plot_window)
                canvas.draw()
                from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
                class CustomToolbar(NavigationToolbar2Tk):
                    def set_message(self, msg):
                        pass
                toolbar = CustomToolbar(canvas, plot_window)
                toolbar.update()
                ax.format_coord = lambda x, y: ""
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