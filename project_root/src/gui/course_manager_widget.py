# src/gui/course_manager_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QFormLayout,
                             QDialogButtonBox, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt


class CourseDialog(QDialog):
    """Dialog for adding/editing a course."""

    def __init__(self, parent=None, course_data=None):
        super().__init__(parent)
        self.course_data = course_data
        self.init_ui()

    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Agregar Curso" if not self.course_data else "Editar Curso")
        self.setModal(True)
        self.resize(400, 300)

        layout = QFormLayout()

        # Code field
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ej: BIJ400, BIJ400L, MAT101")
        layout.addRow("Código del Curso:", self.code_edit)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Biología General")
        layout.addRow("Nombre (opcional):", self.name_edit)

        # Number of groups
        self.groups_spin = QSpinBox()
        self.groups_spin.setMinimum(1)
        self.groups_spin.setMaximum(20)
        self.groups_spin.setValue(1)
        layout.addRow("Número de Grupos:", self.groups_spin)

        # Duration
        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(1)
        self.duration_spin.setMaximum(6)
        self.duration_spin.setValue(2)
        self.duration_spin.setSuffix(" bloques")
        layout.addRow("Duración:", self.duration_spin)

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

        # Load existing data if editing
        if self.course_data:
            self.code_edit.setText(self.course_data.get("code", ""))
            self.name_edit.setText(self.course_data.get("name", ""))
            self.groups_spin.setValue(self.course_data.get("number_of_groups", 1))
            self.duration_spin.setValue(self.course_data.get("duration", 2))
            self.classroom_edit.setText(self.course_data.get("suggested_classroom", "") or "")

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
        return {
            "code": self.code_edit.text().strip(),
            "name": self.name_edit.text().strip() or None,
            "number_of_groups": self.groups_spin.value(),
            "duration": self.duration_spin.value(),
            "suggested_classroom": suggested if suggested else None
        }


class CourseManagerWidget(QWidget):
    """Widget for managing courses."""

    def __init__(self):
        super().__init__()
        self.courses = []
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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Grupos", "Duración", "Aula Sugerida"
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

    def add_course(self):
        """Add a new course."""
        dialog = CourseDialog(self)
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
            
            self.courses.append(course_data)
            self.refresh_table()

    def edit_course(self):
        """Edit the selected course."""
        selected = self.table.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Advertencia", "Por favor seleccione un curso para editar.")
            return

        dialog = CourseDialog(self, self.courses[selected])
        if dialog.exec():
            course_data = dialog.get_course_data()
            
            if not course_data["code"]:
                QMessageBox.warning(self, "Advertencia", "El código del curso es obligatorio.")
                return
            
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

    def get_courses(self):
        """Get the list of courses."""
        return self.courses.copy()
