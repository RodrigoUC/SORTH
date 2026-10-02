"""Shared desktop appearance: readable tables and a single primary action."""

STYLESHEET = """
QWidget { font-family: 'Segoe UI', 'DejaVu Sans', sans-serif; font-size: 10pt; color: #182536; }
QMainWindow, QDialog { background: #f3f6fa; }
QLabel#appTitle { font-size: 24pt; font-weight: 700; color: #154d91; }
QLabel#subtitle { color: #526175; padding-left: 12px; }
QLabel#overview { padding: 12px 0; color: #33465e; font-size: 11pt; }
QLabel#helpText { background: #e7eff9; padding: 12px; border-radius: 6px; }
QPushButton { background: #ffffff; border: 1px solid #aebccc; border-radius: 5px; padding: 8px 14px; }
QPushButton:hover { background: #e9f1fc; border-color: #3974bb; }
QPushButton:pressed { background: #d8e6f8; }
QPushButton:focus, QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 2px solid #1967d2; }
QPushButton:disabled { background: #e7ecf2; color: #627286; border-color: #c8d1dc; }
QPushButton#primaryAction { background: #1967d2; border-color: #1967d2; color: white; font-weight: 600; }
QPushButton#primaryAction:hover { background: #154d91; }
QPushButton#primaryAction:disabled { background: #cbd8e9; border-color: #cbd8e9; color: #485e79; }
QLineEdit, QSpinBox, QComboBox { background: white; border: 1px solid #aebccc; border-radius: 4px; padding: 6px; selection-background-color: #1967d2; }
QTabWidget::pane { border: 1px solid #c8d1dc; background: white; }
QTabBar::tab { padding: 11px 20px; background: #e8edf4; color: #42536a; border: 0; margin-right: 3px; }
QTabBar::tab:selected { background: white; color: #154d91; font-weight: 600; border-bottom: 3px solid #1967d2; }
QTabBar::tab:hover:!selected { background: #dce8f7; }
QTableWidget { background: white; alternate-background-color: #f4f7fb; border: 1px solid #d8e0eb; gridline-color: #e7ecf2; selection-background-color: #d8e8ff; selection-color: #123b6c; }
QHeaderView::section { background: #edf2f8; color: #33465e; padding: 9px 7px; border: 0; border-bottom: 1px solid #d8e0eb; font-weight: 600; }
QStatusBar { background: #edf2f8; color: #42536a; padding: 5px; }
QProgressBar { background: #dde7f4; border: 0; border-radius: 3px; }
QProgressBar::chunk { background: #1967d2; }
"""


def apply_theme(widget):
    widget.setStyleSheet(STYLESHEET)
