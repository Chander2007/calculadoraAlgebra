import tkinter as tk
from SumMultMatrices import MatrixCalculator

def main():
    root = tk.Tk()
    app = MatrixCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
