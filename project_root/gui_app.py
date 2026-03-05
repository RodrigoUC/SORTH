# gui_app.py

"""
SORTH - Sistema de Organización de Horarios
Interfaz gráfica principal

Para ejecutar:
    python gui_app.py
"""

import sys
from pathlib import Path
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def _resolve_icon_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "assets" / "sorth.ico"
    return Path(__file__).parent / "assets" / "sorth.ico"


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SORTH.App")
    except Exception:
        pass


def main():
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("SORTH")
    app.setOrganizationName("SORTH")

    icon_path = _resolve_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
