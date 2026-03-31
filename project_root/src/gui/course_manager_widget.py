# src/gui/course_manager_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QDialog, QLabel,
                             QLineEdit, QSpinBox, QComboBox, QFormLayout,
                             QDialogButtonBox, QMessageBox, QHeaderView, QCheckBox,
                             QTimeEdit)
from PyQt6.QtCore import Qt, QTime, pyqtSignal
from PyQt6.QtWidgets import QCompleter

from ..scheduling.course import Course
from ..scheduling.time_model import TimeModel


def _confirm(parent, title: str, message: str) -> bool:
    """Styled confirmation dialog with colored header."""
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setModal(True)
    dlg.setMinimumWidth(420)

    outer = QVBoxLayout()
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)

    header = QLabel(f"  ⚠️  {title}")
    header.setStyleSheet(
        "background-color: #BF360C; color: #FFFFFF; "
        "font-size: 12pt; font-weight: bold; padding: 14px 20px;"
    )
    outer.addWidget(header)

    body = QWidget()
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(28, 20, 28, 20)
    body_layout.setSpacing(20)

    lbl = QLabel(message)
    lbl.setWordWrap(True)
    lbl.setStyleSheet("font-size: 11pt;")
    body_layout.addWidget(lbl)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
    )
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    body_layout.addWidget(buttons)
    outer.addWidget(body)

    dlg.setLayout(outer)
    return dlg.exec() == QDialog.DialogCode.Accepted


class CourseDialog(QDialog):
    """Dialog for adding/editing a course."""

    DAYS = ["(Sin preferencia)", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

    def __init__(self, parent=None, course: Course = None,
                 completions: list[tuple[str, str]] | None = None):
        super().__init__(parent)
        self.course = course
        self._completions = completions or []   # [(code, name), ...]
        self._code_to_name = {c: n for c, n in self._completions}
        self.setWindowTitle("Agregar Curso" if not course else "Editar Curso")
        self.setModal(True)
        self.resize(460, 420)
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout()

        # Code
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Ej: BIJ400, BIJ400L")
        self.code_edit.textChanged.connect(self._update_room_type_label)
        self.code_edit.textChanged.connect(self._autofill_name)
        if self._completions:
            code_completer = QCompleter([c for c, _ in self._completions])
            code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            code_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.code_edit.setCompleter(code_completer)
        layout.addRow("Código del Curso:", self.code_edit)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ej: Biología General (opcional)")
        if self._completions:
            name_completer = QCompleter([n for _, n in self._completions if n])
            name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            name_completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.name_edit.setCompleter(name_completer)
        layout.addRow("Nombre:", self.name_edit)

        # Number of groups
        self.groups_spin = QSpinBox()
        self.groups_spin.setMinimum(1)
        self.groups_spin.setMaximum(50)
        self.groups_spin.setValue(1)
        layout.addRow("Número de Grupos:", self.groups_spin)

        # Duration — hours + minutes
        dur_layout = QHBoxLayout()
        self.dur_hours = QSpinBox()
        self.dur_hours.setRange(0, 14)
        self.dur_hours.setValue(1)
        self.dur_hours.setSuffix(" h")
        self.dur_mins = QSpinBox()
        self.dur_mins.setRange(0, 55)
        self.dur_mins.setSingleStep(5)
        self.dur_mins.setValue(30)
        self.dur_mins.setSuffix(" min")
        dur_layout.addWidget(self.dur_hours)
        dur_layout.addWidget(self.dur_mins)
        layout.addRow("Duración:", dur_layout)

        # Room type (auto-detected)
        self.room_type_label = QLabel()
        layout.addRow("Tipo de Sala:", self.room_type_label)

        # Suggested classroom
        self.classroom_edit = QLineEdit()
        self.classroom_edit.setPlaceholderText("Ej: 601, LBIO3B (opcional)")
        layout.addRow("Aula Sugerida:", self.classroom_edit)

        # Preferred day
        self.day_combo = QComboBox()
        self.day_combo.addItems(self.DAYS)
        layout.addRow("Día Preferido:", self.day_combo)

        # Preferred start time — QTimeEdit for clarity
        time_layout = QHBoxLayout()
        self.chk_pref_time = QCheckBox("Activar hora preferida")
        self.chk_pref_time.toggled.connect(self._toggle_pref_time)
        self.pref_time_edit = QTimeEdit()
        self.pref_time_edit.setDisplayFormat("HH:mm")
        self.pref_time_edit.setTime(QTime(8, 0))
        self.pref_time_edit.setMinimumTime(QTime(7, 0))
        self.pref_time_edit.setMaximumTime(QTime(21, 0))
        self.pref_time_edit.setToolTip("Hora de inicio preferida para este curso (ej: 08:00, 13:00)")
        time_layout.addWidget(self.chk_pref_time)
        time_layout.addWidget(self.pref_time_edit)
        time_layout.addStretch()
        layout.addRow("Hora Preferida:", time_layout)

        # Split across days
        self.split_combo = QComboBox()
        self.split_combo.addItems([
            "Automático (dividir si > 4.5h)",
            "Forzar división en varios días",
            "No dividir (asignar en un solo día)",
        ])
        self.split_combo.setToolTip(
            "Automático: se divide solo si la duración supera 4.5 horas.\n"
            "Forzar división: siempre se divide en bloques de 2h en días distintos.\n"
            "No dividir: se asigna completo en un solo día sin importar la duración."
        )
        layout.addRow("División en días:", self.split_combo)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

        # Load existing data if editing
        if self.course:
            self.code_edit.setText(self.course.code)
            self.name_edit.setText(self.course.name or "")
            self.groups_spin.setValue(self.course.number_of_groups)
            h, m = divmod(self.course.duration_min, 60)
            self.dur_hours.setValue(h)
            self.dur_mins.setValue(m)
            self.classroom_edit.setText(self.course.suggested_classroom or "")
            if self.course.preferred_day:
                idx = self.day_combo.findText(self.course.preferred_day)
                if idx >= 0:
                    self.day_combo.setCurrentIndex(idx)
            if self.course.preferred_start_min is not None:
                self.chk_pref_time.setChecked(True)
                ph, pm = divmod(self.course.preferred_start_min, 60)
                self.pref_time_edit.setTime(QTime(ph, pm))
            else:
                self.chk_pref_time.setChecked(False)

            # Split
            fs = self.course.force_split
            if fs is True:
                self.split_combo.setCurrentIndex(1)
            elif fs is False:
                self.split_combo.setCurrentIndex(2)
            else:
                self.split_combo.setCurrentIndex(0)

        self._update_room_type_label()
        self._toggle_pref_time(self.chk_pref_time.isChecked())

    def _autofill_name(self, code: str):
        """Auto-fill name when code matches a known course exactly."""
        name = self._code_to_name.get(code.strip())
        if name and not self.name_edit.text():
            self.name_edit.setText(name)

    def _update_room_type_label(self):
        code = self.code_edit.text().strip().upper()
        if code.endswith("L") or code.endswith("P"):
            self.room_type_label.setText("🔬 LAB (detectado automáticamente)")
            self.room_type_label.setStyleSheet("color: #1565C0;")
        else:
            self.room_type_label.setText("🏫 REGULAR (detectado automáticamente)")
            self.room_type_label.setStyleSheet("color: #2E7D32;")

    def _toggle_pref_time(self, enabled: bool):
        self.pref_time_edit.setEnabled(enabled)

    def get_course(self) -> Course | None:
        code = self.code_edit.text().strip()
        if not code:
            return None

        duration_min = self.dur_hours.value() * 60 + self.dur_mins.value()
        if duration_min <= 0:
            duration_min = 60

        code_upper = code.upper()
        room_type = "LAB" if (code_upper.endswith("L") or code_upper.endswith("P")) else "REGULAR"

        preferred_day = self.day_combo.currentText()
        if preferred_day == "(Sin preferencia)":
            preferred_day = None

        preferred_start_min = None
        if self.chk_pref_time.isChecked():
            t = self.pref_time_edit.time()
            preferred_start_min = t.hour() * 60 + t.minute()

        suggested = self.classroom_edit.text().strip() or None

        idx = self.split_combo.currentIndex()
        force_split = None if idx == 0 else (True if idx == 1 else False)

        return Course(
            code=code,
            name=self.name_edit.text().strip() or None,
            number_of_groups=self.groups_spin.value(),
            duration_min=duration_min,
            required_room_type=room_type,
            suggested_classroom=suggested,
            preferred_day=preferred_day,
            preferred_start_min=preferred_start_min,
            force_split=force_split,
        )


class CourseManagerWidget(QWidget):
    """Widget for managing courses to be scheduled."""

    courses_changed = pyqtSignal()  # emitted after any add/edit/delete/clear/load

    def __init__(self, repo=None):
        super().__init__()
        self.courses: list[Course] = []
        self._repo = repo  # SessionRepository, optional
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        info = QLabel(
            "Cursos a programar  —  "
            "Cada curso puede tener múltiples grupos. "
            "El tipo de sala se detecta automáticamente por el código (sufijo L/P → LAB)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #1967D2; color: #FFFFFF; "
            "padding: 10px; border-radius: 4px; font-weight: bold;"
        )
        layout.addWidget(info)

        # Table
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Buscar por código o nombre de curso...")
        self._search.textChanged.connect(self._filter_table)
        search_row.addWidget(self._search)
        layout.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Código", "Nombre", "Grupos", "Duración", "Aula Sugerida",
            "Día Preferido", "Hora Preferida"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ Agregar Curso")
        btn_add.setToolTip("Agregar un nuevo curso manualmente a la lista")
        btn_add.clicked.connect(self._add_course)
        btn_edit = QPushButton("✏️ Editar")
        btn_edit.setToolTip("Editar el curso seleccionado en la tabla")
        btn_edit.clicked.connect(self._edit_course)
        btn_delete = QPushButton("🗑️ Eliminar")
        btn_delete.setToolTip("Eliminar el curso seleccionado de la lista")
        btn_delete.clicked.connect(self._delete_course)
        btn_clear = QPushButton("🧹 Limpiar Todo")
        btn_clear.setToolTip("Eliminar todos los cursos de la lista")
        btn_clear.clicked.connect(self._clear_all)

        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_clear)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_courses_from_excel(self, courses: list[Course]):
        """Load courses imported from Excel, replacing current list."""
        self.courses = list(courses)
        self._search.clear()
        self._refresh_table()
        self.courses_changed.emit()

    def get_courses(self) -> list[Course]:
        return list(self.courses)

    def edit_course_by_code(self, code: str):
        """Open edit dialog for the course with the given code."""
        for i, c in enumerate(self.courses):
            if c.code == code:
                self.table.setCurrentCell(i, 0)
                dialog = CourseDialog(self, self.courses[i], completions=self._get_completions())
                if dialog.exec():
                    course = dialog.get_course()
                    if course:
                        self.courses[i] = course
                        self._refresh_table()
                        self.courses_changed.emit()
                return
        QMessageBox.information(self, "Info",
                                f"El curso {code} no se encuentra en la lista de cursos.")

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _get_completions(self) -> list[tuple[str, str]]:
        if self._repo:
            try:
                return self._repo.get_course_completions()
            except Exception:
                pass
        return []

    def _add_course(self):
        dialog = CourseDialog(self, completions=self._get_completions())
        if dialog.exec():
            course = dialog.get_course()
            if not course:
                QMessageBox.warning(self, "Advertencia", "El código del curso es obligatorio.")
                return
            existing = next((i for i, c in enumerate(self.courses) if c.code == course.code), None)
            if existing is not None:
                if _confirm(self, "Curso ya existe",
                            f"El curso '{course.code}' ya existe en la lista.\n"
                            f"¿Deseas modificarlo en su lugar?"):
                    edit_dlg = CourseDialog(self, self.courses[existing],
                                           completions=self._get_completions())
                    if edit_dlg.exec():
                        updated = edit_dlg.get_course()
                        if updated:
                            self.courses[existing] = updated
                            self._refresh_table()
                            self.courses_changed.emit()
                return
            self.courses.append(course)
            self._refresh_table()
            self.courses_changed.emit()

    def _edit_course(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un curso para editar.")
            return
        dialog = CourseDialog(self, self.courses[row], completions=self._get_completions())
        if dialog.exec():
            course = dialog.get_course()
            if not course:
                QMessageBox.warning(self, "Advertencia", "El código del curso es obligatorio.")
                return
            self.courses[row] = course
            self._refresh_table()
            self.courses_changed.emit()

    def _delete_course(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un curso para eliminar.")
            return
        if _confirm(self, "Confirmar eliminación",
                    f"¿Eliminar el curso {self.courses[row].code}?"):
            del self.courses[row]
            self._refresh_table()
            self.courses_changed.emit()

    def _clear_all(self):
        if not self.courses:
            return
        if _confirm(self, "Confirmar", "¿Eliminar todos los cursos de la lista?\nEsta acción no se puede deshacer."):
            self.courses.clear()
            self._refresh_table()
            self.courses_changed.emit()

    # ------------------------------------------------------------------
    # Table rendering
    # ------------------------------------------------------------------

    def _refresh_table(self):
        self.table.setRowCount(len(self.courses))
        for i, c in enumerate(self.courses):
            h, m = divmod(c.duration_min, 60)
            dur_text = f"{h}h {m:02d}min" if m else f"{h}h"

            pref_time = "—"
            if c.preferred_start_min is not None:
                pref_time = TimeModel.minutes_to_hhmm(c.preferred_start_min)

            self.table.setItem(i, 0, QTableWidgetItem(c.code))
            self.table.setItem(i, 1, QTableWidgetItem(c.name or ""))
            self.table.setItem(i, 2, QTableWidgetItem(str(c.number_of_groups)))
            self.table.setItem(i, 3, QTableWidgetItem(dur_text))
            self.table.setItem(i, 4, QTableWidgetItem(c.suggested_classroom or "—"))
            self.table.setItem(i, 5, QTableWidgetItem(c.preferred_day or "—"))
            self.table.setItem(i, 6, QTableWidgetItem(pref_time))

        self._filter_table(self._search.text())

    def _filter_table(self, text: str):
        text = text.strip().lower()
        for row in range(self.table.rowCount()):
            code = self.table.item(row, 0)
            name = self.table.item(row, 1)
            match = (
                (code and text in code.text().lower()) or
                (name and text in name.text().lower())
            )
            self.table.setRowHidden(row, not match if text else False)
