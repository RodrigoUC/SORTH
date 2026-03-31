# src/gui/main_window.py

import sys
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTabWidget, QStatusBar, QCheckBox, QSpinBox,
                             QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
                             QFormLayout, QLineEdit, QComboBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from .course_manager_widget import CourseManagerWidget
from .schedule_viewer_widget import ScheduleViewerWidget
from ..application.scheduling_service import SchedulingService
from ..infrastructure.excel_reader import ExcelReader
from ..infrastructure.schedule_exporter import ScheduleExporter
from ..scheduling.time_model import TimeModel
from ..scheduling.classroom import Classroom


class ClassroomRestrictionsDialog(QDialog):
    """
    Dialog to configure classroom restrictions.
    Left panel: list of classrooms (checkable).
    Right panel: list of courses for the selected classroom (individually checkable).
    """

    def __init__(self, parent, classroom_course_map: dict[str, list[str]],
                 existing: dict[str, set[str]] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Aulas con Restricciones")
        self.setModal(True)
        self.resize(700, 480)
        self._map = {k: list(v) for k, v in classroom_course_map.items()}
        # Working copy: classroom -> set of selected course codes
        self._selected: dict[str, set[str]] = {}
        if existing:
            for cls, codes in existing.items():
                self._selected[cls] = set(codes)
        self._init_ui()

    def _init_ui(self):
        outer = QVBoxLayout()

        info = QLabel(
            "Active un aula para restringirla. "
            "Luego marque los cursos que pueden usarla (los desmarcados quedan libres)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #1F2937; color: #E5E7EB; "
            "padding: 8px; border-left: 4px solid #3B82F6; border-radius: 4px;"
        )
        outer.addWidget(info)

        split = QHBoxLayout()

        # --- Left: classroom list ---
        left = QVBoxLayout()
        left.addWidget(QLabel("Aulas:"))
        self.cls_list = QListWidget()
        self.cls_list.setMaximumWidth(200)
        for classroom in sorted(self._map):
            item = QListWidgetItem(classroom)
            item.setCheckState(
                Qt.CheckState.Checked if classroom in self._selected
                else Qt.CheckState.Unchecked
            )
            self.cls_list.addItem(item)
        self.cls_list.currentItemChanged.connect(self._on_classroom_selected)
        left.addWidget(self.cls_list)
        split.addLayout(left)

        # --- Right: course list for selected classroom ---
        right = QVBoxLayout()
        self._course_label = QLabel("Seleccione un aula")
        self._course_label.setStyleSheet("font-weight: bold;")
        right.addWidget(self._course_label)
        self.course_list = QListWidget()
        self.course_list.itemChanged.connect(self._on_course_toggled)
        right.addWidget(self.course_list)

        btn_row = QHBoxLayout()
        btn_all = QPushButton("Marcar todos")
        btn_none = QPushButton("Desmarcar todos")
        btn_all.clicked.connect(self._check_all)
        btn_none.clicked.connect(self._uncheck_all)
        btn_row.addWidget(btn_all)
        btn_row.addWidget(btn_none)
        right.addLayout(btn_row)
        split.addLayout(right)

        outer.addLayout(split)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)
        self.setLayout(outer)

        # Select first item
        if self.cls_list.count():
            self.cls_list.setCurrentRow(0)

    def _current_classroom(self) -> str | None:
        item = self.cls_list.currentItem()
        return item.text() if item else None

    def _on_classroom_selected(self, current, _previous):
        if not current:
            return
        classroom = current.text()
        self._course_label.setText(f"Cursos para {classroom}:")
        self.course_list.blockSignals(True)
        self.course_list.clear()
        selected_codes = self._selected.get(classroom, set(self._map.get(classroom, [])))
        for code in sorted(self._map.get(classroom, [])):
            item = QListWidgetItem(code)
            item.setCheckState(
                Qt.CheckState.Checked if code in selected_codes
                else Qt.CheckState.Unchecked
            )
            self.course_list.addItem(item)
        self.course_list.blockSignals(False)

    def _on_course_toggled(self, _item):
        classroom = self._current_classroom()
        if not classroom:
            return
        # Only persist if classroom is checked
        cls_item = self._find_cls_item(classroom)
        if cls_item and cls_item.checkState() == Qt.CheckState.Checked:
            self._save_current_courses(classroom)

    def _find_cls_item(self, classroom: str) -> QListWidgetItem | None:
        for i in range(self.cls_list.count()):
            item = self.cls_list.item(i)
            if item.text() == classroom:
                return item
        return None

    def _save_current_courses(self, classroom: str):
        codes = set()
        for i in range(self.course_list.count()):
            item = self.course_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                codes.add(item.text())
        if codes:
            self._selected[classroom] = codes
        else:
            self._selected.pop(classroom, None)

    def _check_all(self):
        self.course_list.blockSignals(True)
        for i in range(self.course_list.count()):
            self.course_list.item(i).setCheckState(Qt.CheckState.Checked)
        self.course_list.blockSignals(False)
        classroom = self._current_classroom()
        if classroom:
            self._save_current_courses(classroom)

    def _uncheck_all(self):
        self.course_list.blockSignals(True)
        for i in range(self.course_list.count()):
            self.course_list.item(i).setCheckState(Qt.CheckState.Unchecked)
        self.course_list.blockSignals(False)
        classroom = self._current_classroom()
        if classroom:
            self._selected.pop(classroom, None)

    def get_restrictions(self) -> dict[str, set[str]]:
        """Return {classroom: {course_codes}} only for checked+non-empty classrooms."""
        result = {}
        for i in range(self.cls_list.count()):
            item = self.cls_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                classroom = item.text()
                codes = self._selected.get(classroom)
                if not codes:
                    # Default: all courses in map
                    codes = set(self._map.get(classroom, []))
                if codes:
                    result[classroom] = codes
        return result


class AddClassroomDialog(QDialog):
    """Dialog to add a new classroom to the current session."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Agregar Aula")
        self.setModal(True)
        self.setFixedWidth(360)
        self._init_ui()

    def _init_ui(self):
        layout = QFormLayout()
        layout.setSpacing(10)

        self.inp_code     = QLineEdit()
        self.inp_code.setPlaceholderText("Ej: 0601, LBIO5A")
        self.inp_desc     = QLineEdit()
        self.inp_desc.setPlaceholderText("Ej: Aula General")
        self.inp_campus   = QLineEdit()
        self.inp_campus.setPlaceholderText("Ej: HO")
        self.inp_capacity = QSpinBox()
        self.inp_capacity.setRange(1, 500)
        self.inp_capacity.setValue(30)
        self.inp_type     = QComboBox()
        self.inp_type.addItems(["REGULAR", "LAB"])
        self.inp_type.setToolTip(
            "Detectado automáticamente por el código (L al inicio → LAB).\n"
            "Puedes cambiarlo manualmente si es necesario."
        )

        self.inp_code.textChanged.connect(self._update_type_preview)

        layout.addRow("Código *:", self.inp_code)
        layout.addRow("Descripción:", self.inp_desc)
        layout.addRow("Campus:", self.inp_campus)
        layout.addRow("Capacidad *:", self.inp_capacity)
        layout.addRow("Tipo de sala:", self.inp_type)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        outer = QVBoxLayout()
        outer.addLayout(layout)
        outer.addWidget(buttons)
        self.setLayout(outer)

    def _update_type_preview(self, code: str):
        room_type = "LAB" if code.strip().upper().startswith("L") else "REGULAR"
        self.inp_type.setCurrentText(room_type)

    def _on_accept(self):
        if not self.inp_code.text().strip():
            QMessageBox.warning(self, "Error", "El código del aula es obligatorio.")
            return
        self.accept()

    def get_classroom(self) -> Classroom:
        code = self.inp_code.text().strip()
        room_type = self.inp_type.currentText()  # use whatever the user selected
        return Classroom(
            name=code,
            capacity=self.inp_capacity.value(),
            room_type=room_type,
            description=self.inp_desc.text().strip(),
            campus=self.inp_campus.text().strip(),
        )


class SchedulerWorker(QThread):
    finished = pyqtSignal(object, object)   # assignments, groups
    error    = pyqtSignal(str)

    def __init__(self, excel_path, courses, classrooms, restrictions, seed):
        super().__init__()
        self._excel_path   = excel_path
        self._courses      = courses
        self._classrooms   = classrooms
        self._restrictions = restrictions
        self._seed         = seed

    def run(self):
        try:
            service = SchedulingService(self._excel_path, seed=self._seed)
            assignments, groups = service.run(
                courses=self._courses,
                classroom_restrictions=self._restrictions or None,
                classrooms=self._classrooms or None,
            )
            self.finished.emit(assignments, groups)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.excel_path: str | None = None
        self.current_schedule: dict | None = None
        self.current_groups: list | None = None
        self.classroom_restrictions: dict[str, set[str]] = {}
        self._classroom_course_map: dict[str, list[str]] = {}
        self._classrooms: dict[str, Classroom] = {}  # all known classrooms

        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("SORTH - Sistema de Organización de Horarios")
        self._set_window_icon()
        self.setGeometry(100, 100, 1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        main_layout.addLayout(self._create_file_section())

        self.tabs = QTabWidget()
        self.course_manager = CourseManagerWidget()
        self.tabs.addTab(self.course_manager, "📚 Gestión de Cursos")
        self.tabs.setTabToolTip(0, "Ver, agregar, editar y eliminar los cursos a programar")
        self.schedule_viewer = ScheduleViewerWidget()
        self.tabs.addTab(self.schedule_viewer, "📅 Horario Generado")
        self.tabs.setTabToolTip(1, "Visualizar el horario generado en lista, cuadrícula o por aula")
        self.schedule_viewer.edit_course_requested.connect(self._edit_course_from_viewer)
        self.schedule_viewer.group_removed.connect(self._on_group_removed)
        main_layout.addWidget(self.tabs)

        main_layout.addLayout(self._create_actions_section())

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)   # indeterminate
        self._progress.setFixedWidth(160)
        self._progress.setFixedHeight(16)
        self._progress.setVisible(False)
        self.status_bar.addPermanentWidget(self._progress)

        self.status_bar.showMessage("Listo. Cargue un archivo Excel para comenzar.")

    # ------------------------------------------------------------------
    # UI builders
    # ------------------------------------------------------------------

    def _create_file_section(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        info = QLabel(
            "¿Cómo usar SORTH?\n"
            "1️⃣  Cargue un Excel con las hojas Aulas y Cursos (Los nombres de las hojas deben ser 'Aulas' y 'Cursos', respetando minúsculas y mayúsculas).\n"
            "2️⃣  Revise y edite los cursos importados en la pestaña Gestión de Cursos.\n"
            "3️⃣  (Opcional) Configure restricciones de aulas o agregue aulas nuevas.\n"
            "4️⃣  Presione Generar Horario y visualice los resultados."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background-color: #1F2937; color: #E5E7EB; "
            "padding: 12px; border-left: 4px solid #3B82F6; "
            "border-radius: 4px;"
        )
        layout.addWidget(info)

        file_row = QHBoxLayout()
        lbl = QLabel("Archivo Excel:")
        lbl.setStyleSheet("font-weight: bold;")
        self.excel_path_label = QLabel("No seleccionado")
        self.excel_path_label.setStyleSheet("color: #D32F2F; font-style: italic;")

        btn_load = QPushButton("📂 Cargar Excel")
        btn_load.setToolTip(
            "Abrir un archivo Excel (.xlsx) con las hojas:\n"
            "  • Aulas: código, descripción, campus, capacidad\n"
            "  • Cursos: cada fila es un grupo sugerido"
        )
        btn_load.clicked.connect(self._load_excel)
        btn_load.setStyleSheet(
            "QPushButton { background-color: #1967D2; color: white; "
            "padding: 8px 15px; border-radius: 3px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1565C0; }"
        )

        self.btn_add_classroom = QPushButton("🏫 Agregar Aula")
        self.btn_add_classroom.setToolTip(
            "Agregar un aula nueva a la sesión actual.\n"
            "Útil para aulas que no están en el Excel pero deben estar disponibles."
        )
        self.btn_add_classroom.clicked.connect(self._add_classroom)
        self.btn_add_classroom.setStyleSheet(
            "QPushButton { background-color: #6A1B9A; color: white; "
            "padding: 8px 15px; border-radius: 3px; font-weight: bold; }"
            "QPushButton:hover { background-color: #4A148C; }"
        )

        self.btn_restrictions = QPushButton("🔒 Restricciones de Aulas")
        self.btn_restrictions.setToolTip(
            "Configurar qué aulas están reservadas exclusivamente para ciertos cursos.\n"
            "Los cursos restringidos SOLO pueden asignarse a su aula designada."
        )
        self.btn_restrictions.clicked.connect(self._configure_restrictions)
        self.btn_restrictions.setEnabled(False)
        self.btn_restrictions.setStyleSheet(
            "QPushButton { background-color: #E65100; color: white; "
            "padding: 8px 15px; border-radius: 3px; font-weight: bold; }"
            "QPushButton:hover { background-color: #BF360C; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )

        file_row.addWidget(lbl)
        file_row.addWidget(self.excel_path_label, 1)
        file_row.addWidget(btn_load)
        file_row.addWidget(self.btn_add_classroom)
        file_row.addWidget(self.btn_restrictions)
        layout.addLayout(file_row)

        return layout

    def _create_actions_section(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        seed_label = QLabel("🎲 Semilla:")
        seed_label.setToolTip(
            "Controla la aleatoriedad del algoritmo.\n"
            "Semilla fija → mismo horario cada vez (reproducible).\n"
            "Semilla aleatoria → resultados distintos en cada ejecución."
        )

        self.chk_random_seed = QCheckBox("Aleatoria")
        self.chk_random_seed.setToolTip("Activar para usar una semilla aleatoria en cada generación")
        self.chk_random_seed.setChecked(False)

        self.seed_input = QSpinBox()
        self.seed_input.setRange(0, 999999)
        self.seed_input.setValue(42)
        self.seed_input.setPrefix("Valor: ")
        self.seed_input.setToolTip("Valor de semilla fija para resultados reproducibles")
        self.chk_random_seed.toggled.connect(self.seed_input.setDisabled)

        self.btn_generate = QPushButton("🚀 Generar Horario")
        self.btn_generate.setToolTip(
            "Ejecutar el algoritmo de programación con los cursos y aulas cargados.\n"
            "El resultado se muestra en la pestaña Horario Generado."
        )
        self.btn_generate.clicked.connect(self._generate_schedule)
        self.btn_generate.setEnabled(False)
        self.btn_generate.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 10px; font-size: 14px; font-weight: bold; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #cccccc; color: #666666; }"
        )

        self.btn_export = QPushButton("💾 Exportar Resultados")
        self.btn_export.setToolTip(
            "Guardar el horario generado en formato Excel (.xlsx) o CSV.\n"
            "El Excel incluye una grilla visual por aula."
        )
        self.btn_export.clicked.connect(self._export_schedule)
        self.btn_export.setEnabled(False)

        layout.addStretch()
        layout.addWidget(seed_label)
        layout.addWidget(self.chk_random_seed)
        layout.addWidget(self.seed_input)
        layout.addWidget(self.btn_generate)
        layout.addWidget(self.btn_export)

        return layout

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo Excel", "",
            "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return

        try:
            reader = ExcelReader(file_path)
            classrooms = reader.load_classrooms()
            known = set(classrooms.keys())
            courses = reader.load_courses(known_classrooms=known)
            self._classroom_course_map = reader.load_course_classroom_map(known_classrooms=known)
            self._classrooms = classrooms

            self.excel_path = file_path
            self.excel_path_label.setText(Path(file_path).name)
            self.excel_path_label.setStyleSheet("color: green;")

            # Load courses into the manager widget
            self.course_manager.load_courses_from_excel(courses)

            # Reset restrictions when a new file is loaded
            self.classroom_restrictions = {}

            self.btn_generate.setEnabled(True)
            self.btn_restrictions.setEnabled(bool(self._classroom_course_map))

            self.status_bar.showMessage(
                f"✅ Excel cargado: {Path(file_path).name}  "
                f"({len(classrooms)} aulas, {len(courses)} cursos)"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Error al cargar archivo Excel:\n{str(e)}")
            self.excel_path = None
            self.excel_path_label.setText("Error al cargar")
            self.excel_path_label.setStyleSheet("color: red;")

    def _add_classroom(self):
        dialog = AddClassroomDialog(self)
        if not dialog.exec():
            return
        classroom = dialog.get_classroom()
        if classroom.name in self._classrooms:
            QMessageBox.warning(self, "Duplicado",
                                f"El aula '{classroom.name}' ya existe.")
            return
        self._classrooms[classroom.name] = classroom
        self.status_bar.showMessage(
            f"✅ Aula '{classroom.name}' agregada ({classroom.room_type}, cap={classroom.capacity})"
        )

    def _configure_restrictions(self):
        if not self._classroom_course_map:
            QMessageBox.information(self, "Info",
                                    "No hay aulas con cursos asociados en el Excel.")
            return

        dialog = ClassroomRestrictionsDialog(
            self, self._classroom_course_map,
            existing=self.classroom_restrictions or None
        )

        if dialog.exec():
            self.classroom_restrictions = dialog.get_restrictions()
            count = len(self.classroom_restrictions)
            if count:
                self.btn_restrictions.setText(f"🔒 Restricciones ({count})")
                self.status_bar.showMessage(
                    f"✅ {count} aula(s) con restricciones configuradas."
                )
            else:
                self.btn_restrictions.setText("🔒 Aulas con Restricciones")
                self.status_bar.showMessage("Restricciones de aulas eliminadas.")

    def _generate_schedule(self):
        if not self.excel_path:
            QMessageBox.warning(self, "Advertencia",
                                "Por favor cargue un archivo Excel primero.")
            return

        courses = self.course_manager.get_courses()
        if not courses:
            QMessageBox.warning(self, "Advertencia",
                                "Por favor agregue al menos un curso.")
            return

        seed = None if self.chk_random_seed.isChecked() else self.seed_input.value()

        self._worker = SchedulerWorker(
            excel_path=self.excel_path,
            courses=courses,
            classrooms=self._classrooms or None,
            restrictions=self.classroom_restrictions,
            seed=seed,
        )
        self._worker.finished.connect(self._on_schedule_done)
        self._worker.error.connect(self._on_schedule_error)

        self.btn_generate.setEnabled(False)
        self.btn_export.setEnabled(False)
        self._progress.setVisible(True)
        self.status_bar.showMessage("⏳ Generando horario...")
        self._worker.start()

    def _on_schedule_done(self, assignments, groups):
        self._progress.setVisible(False)
        self.btn_generate.setEnabled(True)

        if assignments:
            self.current_schedule = assignments
            self.current_groups   = groups

            courses = self.course_manager.get_courses()
            time_model = TimeModel.default()
            course_name_map = {c.code: c.name for c in courses if c.name}

            self.schedule_viewer.display_schedule(
                assignments, time_model, groups, course_name_map
            )
            self.tabs.setCurrentIndex(1)
            self.btn_export.setEnabled(True)

            total      = len(groups)
            assigned   = len(assignments)
            unassigned = total - assigned

            lines = [
                f"Grupos asignados:    {assigned} / {total}",
                f"Aulas utilizadas:    {len(set(v[0] for v in assignments.values()))}",
                f"Cursos programados:  {len(set(gid.rsplit('-G',1)[0] for gid in assignments))}",
            ]
            if unassigned:
                lines.append(f"\n⚠️  {unassigned} grupo(s) sin asignar.\nRevisa la Lista Detallada (marcados en rojo).")

            self.status_bar.showMessage(f"✅ Horario generado: {assigned}/{total} grupos")
            _InfoDialog(self, "Horario generado", "\n".join(lines)).exec()
        else:
            self.status_bar.showMessage("❌ No se pudo generar el horario")
            dlg = _InfoDialog(
                self, "Sin solución",
                "No se pudo generar un horario válido.\n\n"
                "Posibles causas:\n"
                "  • No hay suficientes aulas disponibles\n"
                "  • Restricciones demasiado estrictas\n"
                "  • Conflictos de horario entre cursos",
                warning=True
            )
            dlg.exec()

    def _on_schedule_error(self, message):
        self._progress.setVisible(False)
        self.btn_generate.setEnabled(True)
        self.status_bar.showMessage("❌ Error al generar horario")
        _InfoDialog(self, "Error", f"Error al generar el horario:\n{message}", warning=True).exec()

    def _export_schedule(self):
        if not self.current_schedule:
            QMessageBox.warning(self, "Advertencia", "No hay horario para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar horario", "horario.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            time_model = TimeModel.default()
            exporter = ScheduleExporter(time_model)
            courses = self.course_manager.get_courses()
            course_name_map = {c.code: c.name for c in courses if c.name}

            if file_path.endswith(".csv"):
                exporter.to_csv(self.current_schedule, file_path,
                                groups=self.current_groups,
                                course_name_by_code=course_name_map)
            else:
                exporter.to_excel(self.current_schedule, file_path,
                                  groups=self.current_groups,
                                  course_name_by_code=course_name_map,
                                  include_grid=True)

            self.status_bar.showMessage(f"✅ Exportado a {Path(file_path).name}")
            _InfoDialog(self, "Éxito", f"Horario exportado a:\n{file_path}").exec()

        except Exception as e:
            _InfoDialog(self, "Error", f"Error al exportar:\n{str(e)}", warning=True).exec()

    def _edit_course_from_viewer(self, course_code: str):
        """Open CourseDialog for the given course code from the schedule viewer."""
        self.tabs.setCurrentIndex(0)
        self.course_manager.edit_course_by_code(course_code)

    def _on_group_removed(self, gid: str):
        if self.current_schedule and gid in self.current_schedule:
            del self.current_schedule[gid]
        if self.current_groups:
            for g in self.current_groups:
                if g.group_id == gid and g.is_assigned():
                    from ..scheduling.schedule_state import ScheduleState
                    # Just clear the assignment reference
                    g.assignment = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _set_window_icon(self):
        try:
            if getattr(sys, 'frozen', False):
                icon_path = Path(sys._MEIPASS) / 'assets' / 'sorth.ico'
            else:
                icon_path = Path(__file__).parent.parent.parent / 'assets' / 'sorth.ico'
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass


class _InfoDialog(QDialog):
    """Styled info/warning dialog with colored header."""

    def __init__(self, parent, title: str, message: str, warning: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)

        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header_color = "#C62828" if warning else "#1967D2"
        icon = "\u26a0\ufe0f" if warning else "\u2705"
        header = QLabel(f"  {icon}  {title}")
        header.setStyleSheet(
            f"background-color: {header_color}; color: #FFFFFF; "
            "font-size: 12pt; font-weight: bold; padding: 14px 20px;"
        )
        outer.addWidget(header)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(28, 20, 28, 20)
        body_layout.setSpacing(20)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setTextFormat(Qt.TextFormat.PlainText)
        lbl.setStyleSheet("font-size: 11pt;")
        lbl.setMinimumWidth(440)
        body_layout.addWidget(lbl)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        body_layout.addWidget(buttons)
        outer.addWidget(body)

        self.setLayout(outer)
