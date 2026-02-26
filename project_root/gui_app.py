# gui_app.py

"""
SORTH - Sistema de Organización de Horarios
Interfaz gráfica principal

Para ejecutar:
    python gui_app.py
"""

import sys
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("SORTH")
    app.setOrganizationName("SORTH")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
