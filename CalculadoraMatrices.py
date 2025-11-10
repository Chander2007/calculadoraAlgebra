import tkinter as tk
from tkinter import messagebox, scrolledtext
from fractions import Fraction

class Matrix:
    def __init__(self, data):
        self.data = data
        self.shape = (len(data), len(data[0]) if data else 0)
    
    def __getitem__(self, key):
        if isinstance(key, tuple):
            i, j = key
            return self.data[i][j]
        else:
            return Matrix([self.data[key]])
    
    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            i, j = key
            self.data[i][j] = value
        else:
            self.data[key] = value.data[0] if isinstance(value, Matrix) else value

class GaussJordanCalculator:
    def __init__(self, root):
        # Permitir montaje dentro de un contenedor (Frame) sin tocar el título/geometry
        self.root = root
        self.colors = {
            "background": "#1C1C1E",       
            "secondary_bg": "#2C2C2E",
            "text": "#FFFFFF",           
            "button_operation": "#FF9F0A", 
            "button_function": "#8E8E93", 
            "button_number": "#505050",   
            "highlight": "#64D2FF"      
        }
        self.operation_color = self.colors["button_operation"]
        self.root.configure(bg=self.colors["background"])
        # Usar el contenedor recibido para construir la UI
        main_frame = tk.Frame(self.root, bg=self.colors["background"])
        main_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        title_label = tk.Label(main_frame, text="Método de Gauss-Jordan", 
                              font=("Arial", 16, "bold"), bg=self.colors["background"], fg=self.colors["text"])
        title_label.pack(pady=10)
        
        input_frame = tk.Frame(main_frame, bg=self.colors["background"])
        input_frame.pack(pady=10)
        
        size_frame = tk.Frame(input_frame, bg=self.colors["background"])
        size_frame.pack(pady=10)
        
        tk.Label(size_frame, text="Número de ecuaciones:", bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=0, padx=5)
        self.num_equations = tk.Spinbox(size_frame, from_=2, to=10, width=5, bg=self.colors["secondary_bg"], fg=self.colors["text"])
        self.num_equations.grid(row=0, column=1, padx=5)
        
        tk.Label(size_frame, text="Número de variables:", bg=self.colors["background"], fg=self.colors["text"]).grid(row=0, column=2, padx=5)
        self.num_variables = tk.Spinbox(size_frame, from_=2, to=10, width=5, bg=self.colors["secondary_bg"], fg=self.colors["text"])
        self.num_variables.grid(row=0, column=3, padx=5)
        
        # Añadir checkbox para modo de vectores
        self.vector_mode_var = tk.BooleanVar()
        self.vector_mode_check = tk.Checkbutton(size_frame, text="Modo Vectores", variable=self.vector_mode_var,
                                               bg=self.colors["background"], fg=self.colors["text"], 
                                               selectcolor=self.colors["secondary_bg"], activebackground=self.colors["background"],
                                               activeforeground=self.colors["text"])
        self.vector_mode_check.grid(row=0, column=4, padx=10)
        
        create_btn = tk.Button(input_frame, text="Crear Matriz", command=self.create_matrix,
                              bg=self.colors["button_operation"], fg=self.colors["text"], font=("Arial", 10, "bold"))
        create_btn.pack(pady=10)
        
        self.matrix_frame = tk.Frame(main_frame, bg=self.colors["background"])
        self.matrix_frame.pack(pady=10, fill="both")
        
        button_frame = tk.Frame(main_frame, bg=self.colors["background"])
        button_frame.pack(pady=10)
        
        solve_btn = tk.Button(button_frame, text="Resolver", command=self.solve,
                             bg=self.colors["button_operation"], fg=self.colors["text"], font=("Arial", 10, "bold"))
        solve_btn.grid(row=0, column=0, padx=10)
        
        clear_btn = tk.Button(button_frame, text="Limpiar", command=self.clear,
                             bg=self.colors["button_function"], fg=self.colors["text"], font=("Arial", 10, "bold"))
        clear_btn.grid(row=0, column=1, padx=10)
        
        result_label = tk.Label(main_frame, text="Solución paso a paso:", 
                               font=("Arial", 12, "bold"), bg=self.colors["background"], fg=self.colors["text"])
        result_label.pack(pady=(20, 5), anchor="w")
        
        self.result_text = scrolledtext.ScrolledText(main_frame, width=80, height=15, 
                                                    font=("Courier New", 10), bg=self.colors["secondary_bg"], fg=self.colors["text"])
        self.result_text.pack(pady=5, fill="both", expand=True)
        
        self.configure_text_tags()
        
        self.result_text.tag_configure("step", foreground=self.colors["button_operation"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("matrix", foreground=self.colors["highlight"])
        self.result_text.tag_configure("free_var_info", foreground="#30D158")
        self.result_text.tag_configure("title", foreground=self.colors["highlight"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("subtitle", foreground=self.colors["button_operation"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("value", foreground=self.colors["text"])
        self.result_text.tag_configure("free_var", foreground="#30D158")  
        self.result_text.tag_configure("solution_type", foreground=self.colors["highlight"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("note", foreground="#64D2FF")  
        self.result_text.tag_configure("var_name", foreground=self.colors["button_operation"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("var_value", foreground="#FFFFFF")
        self.result_text.tag_configure("operator", foreground="#FF9F0A")
        self.result_text.tag_configure("coefficient", foreground="#BF5AF2")  
        self.result_text.tag_configure("inconsistent", foreground="#FF453A")
        self.result_text.tag_configure("independent", foreground="#30D158", font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("dependent", foreground="#FF453A", font=("Courier New", 10, "bold"))
        
        self.entries = []
        self.matrix = None
        
    def create_matrix(self):
        for widget in self.matrix_frame.winfo_children():
            widget.destroy()
        
        rows = int(self.num_equations.get())
        cols = int(self.num_variables.get()) + 1 
        
        # Si estamos en modo vectores, no mostramos la columna de términos independientes
        vector_mode = self.vector_mode_var.get()
        if vector_mode:
            cols = int(self.num_variables.get())
        
        for j in range(cols if not vector_mode else cols):  
            var_label = tk.Label(self.matrix_frame, text=f"x{j+1}", bg=self.colors["background"], fg=self.colors["highlight"])
            var_label.grid(row=0, column=j*2)
        
        self.entries = []
        for i in range(rows):
            row_entries = []
            for j in range(cols):
                if j == cols - 1 and not vector_mode:
                    tk.Label(self.matrix_frame, text="=", bg=self.colors["background"], fg=self.colors["text"]).grid(row=i+1, column=j*2-1)
                
                entry = tk.Entry(self.matrix_frame, width=5, bg=self.colors["secondary_bg"], fg=self.colors["text"], insertbackground=self.colors["text"])
                entry.grid(row=i+1, column=j*2, padx=5, pady=5)
                row_entries.append(entry)
                
                if j < cols - 2 or (vector_mode and j < cols - 1):
                    op_label = tk.Label(self.matrix_frame, text="+", bg=self.colors["background"], fg=self.colors["button_operation"])
                    op_label.grid(row=i+1, column=j*2+1)
            
            self.entries.append(row_entries)
    
    def get_matrix(self):
        rows = len(self.entries)
        cols = len(self.entries[0])
        matrix = []
        
        for i in range(rows):
            row = []
            for j in range(cols):
                try:
                    value = self.entries[i][j].get().strip()
                    if '/' in value:
                        num, den = value.split('/')
                        val = Fraction(int(num), int(den))
                    else:
                        val = Fraction(value)
                    row.append(val)
                except ValueError:
                    messagebox.showerror("Error", f"Valor inválido en fila {i+1}, columna {j+1}")
                    return None
            matrix.append(row)
        
        return matrix
    
    def solve(self):
        matrix = self.get_matrix()
        if matrix is None:
            return
        
        # Si estamos en modo vectores, añadimos una columna de ceros para representar el sistema homogéneo
        vector_mode = self.vector_mode_var.get()
        if vector_mode:
            for row in matrix:
                row.append(Fraction(0))
        
        self.matrix = Matrix(matrix)
        
        self.result_text.delete(1.0, tk.END)
        
        self.result_text.insert(tk.END, "Matriz original:\n", "step")
        self.display_matrix(self.matrix)
        self.result_text.insert(tk.END, "\n")
        
        n_rows, n_cols = self.matrix.shape
        pivot_columns = []
        free_variables = []
        
        for i in range(n_rows):
            pivot_found = self.process_row(i, pivot_columns, free_variables)
            
            self.show_current_state(pivot_columns, free_variables)
        
        self.analyze_system(pivot_columns, free_variables)
    
    def process_row(self, i, pivot_columns, free_variables):
        """Procesa una fila en el método de Gauss-Jordan"""
        n_rows, n_cols = self.matrix.shape
        n_vars = n_cols - 1
        
        pivot_found = False
        for j in range(i, n_rows):
            if j < n_cols - 1 and self.matrix[j, i] != 0:  
                if j != i:
                    # Intercambiar filas
                    temp_row = self.matrix.data[i][:]
                    self.matrix.data[i] = self.matrix.data[j][:]
                    self.matrix.data[j] = temp_row
                    
                    self.result_text.insert(tk.END, f"Intercambiar fila {i+1} con fila {j+1}:\n", "step")
                    self.display_matrix(self.matrix)
                    self.result_text.insert(tk.END, "\n")
                
                pivot_found = True
                pivot_columns.append(i)
                break
        
        if pivot_found:
            pivot = self.matrix[i, i]
            if pivot != 1:
                # Dividir fila por el pivote
                for k in range(n_cols):
                    self.matrix.data[i][k] = self.matrix.data[i][k] / pivot
                
                self.result_text.insert(tk.END, f"Dividir fila {i+1} por {self.fraction_to_str(pivot)}:\n", "step")
                self.display_matrix(self.matrix)
                self.result_text.insert(tk.END, "\n")
            
            for k in range(n_rows):
                if k != i and self.matrix[k, i] != 0:
                    factor = self.matrix[k, i]
                    # Restar factor * fila_pivote de la fila actual
                    for j in range(n_cols):
                        self.matrix.data[k][j] = self.matrix.data[k][j] - factor * self.matrix.data[i][j]
                    
                    self.result_text.insert(tk.END, f"Restar {self.fraction_to_str(factor)} veces la fila {i+1} de la fila {k+1}:\n", "step")
                    self.display_matrix(self.matrix)
                    self.result_text.insert(tk.END, "\n")
        else:
            if i < n_cols - 1: 
                free_variables.append(i)
                self.result_text.insert(tk.END, f"La variable x{i+1} es una variable libre\n", "free_var_info")
        
        return pivot_found
    
    def show_current_state(self, pivot_columns, free_variables):
        """Muestra el estado actual del sistema"""
        n_rows, n_cols = self.matrix.shape
        n_vars = n_cols - 1
        
        current_free_vars = [j+1 for j in range(n_vars) if j not in pivot_columns and j not in free_variables]
        
        self.result_text.insert(tk.END, "\nEstado actual:\n", "step")
        self.result_text.insert(tk.END, f"Columnas pivote encontradas: {[col+1 for col in pivot_columns]}\n", "matrix")
        
        all_free_vars = free_variables + current_free_vars
        if all_free_vars:
            self.result_text.insert(tk.END, f"Variables libres identificadas: x{', x'.join(map(str, [v+1 for v in free_variables]))}", "free_var_info")
            if current_free_vars:
                self.result_text.insert(tk.END, f" (potenciales adicionales: x{', x'.join(map(str, current_free_vars))})", "matrix")
            self.result_text.insert(tk.END, "\n\n")
        else:
            self.result_text.insert(tk.END, "No se han identificado variables libres aún\n\n", "matrix")
    
    def analyze_system(self, pivot_columns, free_variables):
        n_rows, n_cols = self.matrix.shape
        n_vars = n_cols - 1
        
        inconsistent = self.check_consistency()
        
        self.result_text.insert(tk.END, "\nANÁLISIS FINAL DEL SISTEMA:\n", "title")
        self.result_text.insert(tk.END, "=========================\n", "title")
        
        if inconsistent:
            self.result_text.insert(tk.END, "El sistema es INCONSISTENTE (no tiene solución).\n", "inconsistent")
        else:
            self.show_system_analysis(pivot_columns, n_vars)
            self.show_solution(pivot_columns, n_vars)
            
            # Verificar independencia lineal si estamos en modo vectores
            if self.vector_mode_var.get():
                self.check_linear_independence(pivot_columns, n_vars)
    
    def check_consistency(self):
        """Verifica si el sistema es consistente"""
        n_rows, n_cols = self.matrix.shape
        n_vars = n_cols - 1
        
        for i in range(n_rows):
            if all(self.matrix.data[i][j] == 0 for j in range(n_vars)) and self.matrix.data[i][-1] != 0:
                return True
        return False
    
    def check_linear_independence(self, pivot_columns, n_vars):
        """Verifica si los vectores son linealmente independientes"""
        self.result_text.insert(tk.END, "\nANÁLISIS DE INDEPENDENCIA LINEAL:\n", "title")
        self.result_text.insert(tk.END, "=============================\n", "title")
        
        if len(pivot_columns) == n_vars:
            self.result_text.insert(tk.END, "Los vectores son LINEALMENTE INDEPENDIENTES.\n", "independent")
            self.result_text.insert(tk.END, "Explicación: El número de columnas pivote es igual al número de variables, lo que significa que no hay variables libres y la única solución del sistema homogéneo es la trivial (todos ceros).\n", "note")
        else:
            self.result_text.insert(tk.END, "Los vectores son LINEALMENTE DEPENDIENTES.\n", "dependent")
            self.result_text.insert(tk.END, f"Explicación: Hay {n_vars - len(pivot_columns)} variables libres, lo que significa que el sistema homogéneo tiene infinitas soluciones no triviales.\n", "note")
    
    def show_system_analysis(self, pivot_columns, n_vars):
        """Muestra el análisis del sistema"""
        self.result_text.insert(tk.END, "Columnas pivote: ", "subtitle")
        self.result_text.insert(tk.END, f"{[col+1 for col in pivot_columns]}\n", "value")
        
        free_vars = [i+1 for i in range(n_vars) if i not in pivot_columns]
        if free_vars:
            self.result_text.insert(tk.END, "Variables libres: ", "subtitle")
            self.result_text.insert(tk.END, f"x{', x'.join(map(str, free_vars))}\n", "free_var")
            self.result_text.insert(tk.END, "El sistema tiene INFINITAS SOLUCIONES.\n", "solution_type")
            self.result_text.insert(tk.END, "Cada variable libre puede tomar cualquier valor real.\n", "note")
        else:
            self.result_text.insert(tk.END, "No hay variables libres.\n", "subtitle")
            self.result_text.insert(tk.END, "El sistema tiene SOLUCIÓN ÚNICA.\n", "solution_type")
    
    def show_solution(self, pivot_columns, n_vars):
        """Muestra la solución del sistema"""
        n_rows, n_cols = self.matrix.shape
        free_vars = [i+1 for i in range(n_vars) if i not in pivot_columns]
        
        self.result_text.insert(tk.END, "\nSOLUCIÓN FINAL:\n", "title")
        self.result_text.insert(tk.END, "=============\n", "title")
        
        if not free_vars:
            self.show_unique_solution(pivot_columns, n_vars, n_rows)
        else:  
            self.show_parametric_solution(pivot_columns, free_vars)
    
    def show_unique_solution(self, pivot_columns, n_vars, n_rows):
        """Muestra la solución única del sistema"""
        for i in range(min(n_vars, n_rows)):
            if i in pivot_columns:
                var_idx = pivot_columns.index(i)
                self.result_text.insert(tk.END, f"x{i+1} = ", "var_name")
                self.result_text.insert(tk.END, f"{self.fraction_to_str(self.matrix.data[var_idx][-1])}\n", "var_value")
    
    def show_parametric_solution(self, pivot_columns, free_vars):
        """Muestra la solución paramétrica en términos de variables libres"""
        self.result_text.insert(tk.END, "Variables dependientes en términos de variables libres:\n", "subtitle")
        for i in range(len(pivot_columns)):
            pivot_col = pivot_columns[i]
            self.result_text.insert(tk.END, f"x{pivot_col+1} = ", "var_name")
            self.result_text.insert(tk.END, f"{self.fraction_to_str(self.matrix.data[i][-1])}", "var_value")
            
            for j in free_vars:
                coef = -self.matrix.data[i][j-1] 
                if coef != 0:
                    sign = "-" if coef > 0 else "+"
                    coef_str = self.fraction_to_str(abs(coef))
                    self.result_text.insert(tk.END, f" {sign} ", "operator")
                    self.result_text.insert(tk.END, f"{coef_str}", "coefficient")
                    self.result_text.insert(tk.END, f"x{j}", "free_var")
            
            self.result_text.insert(tk.END, "\n")
        
        self.result_text.insert(tk.END, "\nVariables libres:\n", "subtitle")
        for j in free_vars:
            self.result_text.insert(tk.END, f"x{j} ", "free_var")
            self.result_text.insert(tk.END, "puede tomar cualquier valor real\n", "note")
    
    def display_matrix(self, matrix):
        rows, cols = matrix.shape
        for i in range(rows):
            row_str = "  "
            for j in range(cols):
                val = self.fraction_to_str(matrix.data[i][j])
                row_str += f"{val:>8}  "
            self.result_text.insert(tk.END, row_str + "\n")
    
    def configure_text_tags(self):
        """Centraliza la configuración de todas las etiquetas de texto"""
        self.result_text.tag_configure("step", foreground=self.colors["button_operation"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("matrix", foreground=self.colors["highlight"])
        self.result_text.tag_configure("free_var_info", foreground="#30D158")
        self.result_text.tag_configure("title", foreground=self.colors["highlight"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("subtitle", foreground=self.colors["button_operation"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("value", foreground=self.colors["text"])
        self.result_text.tag_configure("free_var", foreground="#30D158")  
        self.result_text.tag_configure("solution_type", foreground=self.colors["highlight"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("note", foreground="#64D2FF")  
        self.result_text.tag_configure("var_name", foreground=self.colors["button_operation"], font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("var_value", foreground="#FFFFFF")
        self.result_text.tag_configure("operator", foreground="#FF9F0A")
        self.result_text.tag_configure("coefficient", foreground="#BF5AF2")  
        self.result_text.tag_configure("inconsistent", foreground="#FF453A")  
        self.result_text.tag_configure("independent", foreground="#30D158", font=("Courier New", 10, "bold"))
        self.result_text.tag_configure("dependent", foreground="#FF453A", font=("Courier New", 10, "bold"))
    
    def fraction_to_str(self, frac):
        if isinstance(frac, Fraction):
            if frac.denominator == 1:
                return str(frac.numerator)
            else:
                return f"{frac.numerator}/{frac.denominator}"
        return str(frac)
    
    def clear(self):
        for row in self.entries:
            for entry in row:
                entry.delete(0, tk.END)
        
        self.result_text.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = GaussJordanCalculator(root)
    root.mainloop()