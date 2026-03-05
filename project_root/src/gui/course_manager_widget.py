# src/gui/course_manager_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QFormLayout,
                             QDialogButtonBox, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import QStringListModel
import json
from pathlib import Path


class CourseDialog(QDialog):
    """Dialog for adding/editing a course."""

    def __init__(self, parent=None, course_data=None, code_history=None, name_history=None, duration_history=None):
        super().__init__(parent)
        self.course_data = course_data
        self.code_history = code_history or []
        self.name_history = name_history or []
        self.duration_history = duration_history or []
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Agregar Curso" if not self.course_data else "Editar Curso")
        self.setModal(True)
        self.resize(450, 400)

        layout = QFormLayout()

        # Code field with autocomplete
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ej: BIJ400, BIJ400L, QUX103")
        code_completer = QCompleter(self.code_history)
        code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.code_edit.setCompleter(code_completer)
        layout.addRow("Código del Curso:", self.code_edit)

        # Name field with autocomplete
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Biología General")
        name_completer = QCompleter(self.name_history)
        name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_edit.setCompleter(name_completer)
        layout.addRow("Nombre (opcional):", self.name_edit)

        # Number of groups
        self.groups_spin = QSpinBox()
        self.groups_spin.setMinimum(1)
        self.groups_spin.setMaximum(20)
        self.groups_spin.setValue(1)
        layout.addRow("Número de Grupos:", self.groups_spin)

        # Duration with history suggestions
        self.duration_combo = QComboBox()
        # Add unique durations from history, then add defaults
        duration_options = sorted(set(self.duration_history + [1, 2, 3, 4, 5, 6]))
        for duration in duration_options[:6]:  # Limit to 6
            self.duration_combo.addItem(f"{duration} bloque(s)", duration)
        self.duration_combo.setCurrentIndex(1)  # Default to 2 blocks
        layout.addRow("Duración:", self.duration_combo)

        # Room type (informational)
        self.room_type_label = QLabel()
        self.room_type_label.setStyleSheet("color: gray; font-style: italic;")
        self.update_room_type_display()
        self.code_edit.textChanged.connect(self.update_room_type_display)
        layout.addRow("Tipo de Sala:", self.room_type_label)

        # Suggested classroom
        self.classroom_edit = QLineEdit()
        self.classroom_edit.setPlaceholderText("Ej: 601, L301 (opcional)")
        layout.addRow("Aula Sugerida:", self.classroom_edit)

        # Preferred day (optional)
        self.preferred_day_combo = QComboBox()
        self.preferred_day_combo.addItems([
            "(Sin preferencia)",
            "Lunes",
            "Martes",
            "Miércoles",
            "Jueves",
            "Viernes",
            "Sábado"
        ])
        layout.addRow("Día Preferido (opcional):", self.preferred_day_combo)

        # Preferred hour (optional)
        self.preferred_hour_combo = QComboBox()
        self.preferred_hour_combo.addItems([
            "(Sin preferencia)",
            "7:00", "8:00", "9:00", "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"
        ])
        layout.addRow("Hora Preferida (opcional):", self.preferred_hour_combo)

        # Load existing data if editing
        if self.course_data:
            self.code_edit.setText(self.course_data.get("code", ""))
            self.name_edit.setText(self.course_data.get("name", ""))
            self.groups_spin.setValue(self.course_data.get("number_of_groups", 1))
            
            # Load duration
            duration = self.course_data.get("duration", 2)
            index = self.duration_combo.findData(duration)
            if index >= 0:
                self.duration_combo.setCurrentIndex(index)
            
            self.classroom_edit.setText(self.course_data.get("suggested_classroom", "") or "")
            
            # Load preferred day
            preferred_day = self.course_data.get("preferred_day")
            if preferred_day:
                index = self.preferred_day_combo.findText(preferred_day)
                if index >= 0:
                    self.preferred_day_combo.setCurrentIndex(index)
            
            # Load preferred hour
            preferred_hour = self.course_data.get("preferred_hour")
            if preferred_hour:
                hour_text = f"{preferred_hour}:00"
                index = self.preferred_hour_combo.findText(hour_text)
                if index >= 0:
                    self.preferred_hour_combo.setCurrentIndex(index)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def update_room_type_display(self):
        """Update the room type display based on code."""
        code = self.code_edit.text().strip().upper()
        if code.endswith('L') or code.endswith('P'):
            self.room_type_label.setText("🔬 LAB (detectado automáticamente)")
            self.room_type_label.setStyleSheet("color: blue;")
        else:
            self.room_type_label.setText("🏫 REGULAR (detectado automáticamente)")
            self.room_type_label.setStyleSheet("color: green;")

    def get_course_data(self):
        """Get the course data from the form."""
        suggested = self.classroom_edit.text().strip()
        
        # Get preferred day (None if no preference)
        preferred_day_text = self.preferred_day_combo.currentText()
        preferred_day = None if preferred_day_text == "(Sin preferencia)" else preferred_day_text
        
        # Get preferred hour (None if no preference)
        preferred_hour_text = self.preferred_hour_combo.currentText()
        preferred_hour = None
        if preferred_hour_text != "(Sin preferencia)":
            preferred_hour = int(preferred_hour_text.split(":")[0])
        
        return {
            "code": self.code_edit.text().strip(),
            "name": self.name_edit.text().strip() or None,
            "number_of_groups": self.groups_spin.value(),
            "duration": self.duration_combo.currentData(),
            "suggested_classroom": suggested if suggested else None,
            "preferred_day": preferred_day,
            "preferred_hour": preferred_hour
        }


class CourseManagerWidget(QWidget):
    """Widget for managing courses."""

    HISTORY_FILE = Path.home() / ".sorth_course_history.json"

    def __init__(self):
        super().__init__()
        self.courses = []
        self.code_history = []
        self.name_history = []
        self.duration_history = []
        self._load_history()
        self.init_ui()

    def init_ui(self):
        """Initialize the widget UI."""
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Gestión de Cursos\n\n"
            "Agregue los cursos que desea programar. El tipo de sala (LAB/REGULAR) se detecta "
            "automáticamente del código:\n"
            "• Termina en 'L' o 'P' → LAB\n"
            "• De lo contrario → REGULAR"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(
            "background-color: #1967D2; "
            "color: #FFFFFF; "
            "padding: 15px; "
            "border-radius: 5px; "
            "font-weight: bold;"
        )
        layout.addWidget(instructions)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Grupos", "Duración", "Aula Sugerida", "Día Preferido", "Hora Preferida"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Agregar Curso")
        btn_add.clicked.connect(self.add_course)
        
        btn_edit = QPushButton("✏️ Editar")
        btn_edit.clicked.connect(self.edit_course)
        
        btn_delete = QPushButton("🗑️ Eliminar")
        btn_delete.clicked.connect(self.delete_course)
        
        btn_clear = QPushButton("🧹 Limpiar Todo")
        btn_clear.clicked.connect(self.clear_all)
        
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        button_layout.addStretch()
        button_layout.addWidget(btn_clear)
        
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_history(self):
        """Load course history from file."""
        if self.HISTORY_FILE.exists():
            try:
                with open(self.HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    self.code_history = history.get("codes", [])
                    self.name_history = history.get("names", [])
                    self.duration_history = history.get("durations", [])
            except Exception as e:
                print(f"Error loading history: {e}")

    def _save_history(self):
        """Save course history to file."""
        try:
            history = {
                "codes": self.code_history,
                "names": self.name_history,
                "durations": self.duration_history
            }
            with open(self.HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_course(self):
        """Add a new course."""
        dialog = CourseDialog(self, None, self.code_history, self.name_history, self.duration_history)
        if dialog.exec():
            course_data = dialog.get_course_data()
            
            if not course_data["code"]:
                QMessageBox.warning(self, "Advertencia", "El código del curso es obligatorio.")
                return
            
            # Check for duplicates
            if any(c["code"] == course_data["code"] for c in self.courses):
                QMessageBox.warning(
                    self, 
                    "Advertencia", 
                    f"Ya existe un curso con el código {course_data['code']}"
                )
                return
            
            # Update history
            if course_data["code"] and course_data["code"] not in self.code_history:
                self.code_history.append(course_data["code"])
            if course_data["name"] and course_data["name"] not in self.name_history:
                self.name_history.append(course_data["name"])
            if course_data["duration"] and course_data["duration"] not in self.duration_history:
                self.duration_history.append(course_data["duration"])
            self._save_history()
            
            self.courses.append(course_data)
            self.refresh_table()

    def edit_course(self):
        """Edit the selected course."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione un curso para editar.")
            return

        dialog = CourseDialog(self, self.courses[selected], self.code_history, self.name_history, self.duration_history)
        if dialog.exec():
            course_data = dialog.get_course_data()
            
            if not course_data["code"]:
                QMessageBox.warning(self, "Advertencia", "El código del curso es obligatorio.")
                return
            
            # Update history
            if course_data["code"] and course_data["code"] not in self.code_history:
                self.code_history.append(course_data["code"])
            if course_data["name"] and course_data["name"] not in self.name_history:
                self.name_history.append(course_data["name"])
            if course_data["duration"] and course_data["duration"] not in self.duration_history:
                self.duration_history.append(course_data["duration"])
            self._save_history()
            
            self.courses[selected] = course_data
            self.refresh_table()

    def delete_course(self):
        """Delete the selected course."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione un curso para eliminar.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el curso {self.courses[selected]['code']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.courses[selected]
            self.refresh_table()

    def clear_all(self):
        """Clear all courses."""
        if not self.courses:
            return

        reply = QMessageBox.question(
            self,
            "Confirmar limpieza",
            "¿Está seguro de eliminar todos los cursos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.courses.clear()
            self.refresh_table()

    def refresh_table(self):
        """Refresh the table display."""
        self.table.setRowCount(len(self.courses))
        
        for i, course in enumerate(self.courses):
            self.table.setItem(i, 0, QTableWidgetItem(course["code"]))
            self.table.setItem(i, 1, QTableWidgetItem(course.get("name", "") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(str(course["number_of_groups"])))
            self.table.setItem(i, 3, QTableWidgetItem(f"{course['duration']} bloques"))
            self.table.setItem(i, 4, QTableWidgetItem(course.get("suggested_classroom", "") or ""))
            self.table.setItem(i, 5, QTableWidgetItem(course.get("preferred_day", "") or "-"))
            
            # Format preferred hour
            preferred_hour = course.get("preferred_hour")
            hour_text = f"{preferred_hour}:00" if preferred_hour else "-"
            self.table.setItem(i, 6, QTableWidgetItem(hour_text))

    def get_courses(self):
        """Get the list of courses."""
        return self.courses.copy()
