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

    app.setStyleSheet("""
        * { font-size: 10pt; }
        QHeaderView::section { font-size: 10pt; font-weight: bold; }
        QTabBar::tab {
            font-size: 10pt;
            padding: 8px 16px;
            color: #555555;
            background-color: #E0E0E0;
            border: 1px solid #BDBDBD;
            border-bottom: none;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #1967D2;
            color: #FFFFFF;
            font-weight: bold;
            border-color: #1967D2;
        }
        QTabBar::tab:hover:!selected {
            background-color: #BBDEFB;
            color: #1B1B1B;
        }
    """)

    icon_path = _resolve_icon_path()
    icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    if not icon.isNull():
        app.setWindowIcon(icon)

    window = MainWindow()
    if not icon.isNull():
        window.setWindowIcon(icon)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
