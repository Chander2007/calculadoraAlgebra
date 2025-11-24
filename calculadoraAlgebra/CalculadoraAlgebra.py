from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
try:
    from .CalculadoraAlgebraQt import MainWindow
except ImportError:
    from CalculadoraAlgebraQt import MainWindow

def main():
    app = QApplication([])
    w = MainWindow()
    w.showMaximized()
    app.exec()

if __name__ == "__main__":
    main()