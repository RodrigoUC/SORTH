# src/gui/main_window.py

import sys
from pathlib import Path

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTabWidget, QStatusBar, QCheckBox, QSpinBox,
                             QDialog, QDialogButtonBox, QProgressBar, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from .course_manager_widget import CourseManagerWidget
from .schedule_viewer_widget import ScheduleViewerWidget
from ..infrastructure.excel_reader import ExcelReader
from ..infrastructure.schedule_exporter import ScheduleExporter
from ..infrastructure.session_repository import SessionRepository
from ..scheduling.time_model import TimeModel
from ..scheduling.classroom import Classroom

from .dialogs import ClassroomRestrictionsDialog, AddClassroomDialog, _InfoDialog
from .scheduler_worker import SchedulerWorker
from .theme import apply_theme
from .motion import MotionController, update_busy_indicator


class MainWindow(QMainWindow):

    def __init__(self, repo=None, restore_session=True):
        super().__init__()
        self._busy = False
        self._loading = False
        self._worker = None
        self.excel_path: str | None = None
        self.current_schedule: dict | None = None
        self.current_groups: list | None = None
        self.classroom_restrictions: dict[str, set[str]] = {}
        self._classroom_course_map: dict[str, list[str]] = {}
        self._classrooms: dict[str, Classroom] = {}
        self._repo = repo if repo is not None else SessionRepository()

        self._motion = MotionController(self)
        self._init_ui()
        if restore_session:
            self._restore_session_if_exists()

    def _init_ui(self):
        self.setWindowTitle("SORTH - Sistema de Organización de Horarios")
        self._set_window_icon()
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(960, 640)
        apply_theme(self)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 20, 24, 12)
        main_layout.setSpacing(16)

        main_layout.addLayout(self._create_file_section())

        self.tabs = QTabWidget()
        self.course_manager = CourseManagerWidget(repo=self._repo)
        self.tabs.addTab(self.course_manager, "📚 Gestión de Cursos")
        self.tabs.setTabToolTip(0, "Ver, agregar, editar y eliminar los cursos a programar")
        self.course_manager.courses_changed.connect(self._on_inputs_changed)
        self.schedule_viewer = ScheduleViewerWidget()
        self.tabs.addTab(self.schedule_viewer, "📅 Horario Generado")
        self.tabs.setTabToolTip(1, "Visualizar el horario generado en lista, cuadrícula o por aula")
        self.schedule_viewer.edit_course_requested.connect(self._edit_course_from_viewer)
        self.schedule_viewer.group_removed.connect(self._on_group_removed)
        self.schedule_viewer.schedule_cleared.connect(self._on_schedule_cleared)
        main_layout.addWidget(self.tabs, 1)
        self.tabs.currentChanged.connect(
            lambda _index: self._motion.reveal(self.tabs.currentWidget()))
        self.schedule_viewer.tabs.currentChanged.connect(
            lambda _index: self._motion.reveal(self.schedule_viewer.tabs.currentWidget()))

        main_layout.addLayout(self._create_actions_section())

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)   # indeterminate
        self._progress.setFixedWidth(160)
        self._progress.setFixedHeight(16)
        self._progress.setVisible(False)
        self.status_bar.addPermanentWidget(self._progress)

        self.chk_reduce_motion = QCheckBox("Reducir animaciones")
        self.chk_reduce_motion.setToolTip("Desactiva las transiciones y el indicador animado.")
        self.chk_reduce_motion.setChecked(self._motion.reduced)
        self.chk_reduce_motion.toggled.connect(self._set_reduced_motion)
        self.status_bar.addPermanentWidget(self.chk_reduce_motion)
        update_busy_indicator(self._progress, False, self._motion.reduced)

        self.status_bar.showMessage("Listo. Cargue un archivo Excel para comenzar.")

    # ------------------------------------------------------------------
    # UI builders
    # ------------------------------------------------------------------

    def _create_file_section(self) -> QVBoxLayout:
        layout = QVBoxLayout()

        header = QFrame()
        header.setObjectName("brandHeader")
        heading = QHBoxLayout(header)
        heading.setContentsMargins(16, 6, 16, 6)
        title = QLabel("SORTH")
        title.setObjectName("appTitle")
        heading.addWidget(title)
        subtitle = QLabel("Organización de horarios académicos")
        subtitle.setObjectName("subtitle")
        heading.addWidget(subtitle)
        heading.addStretch()
        help_button = QPushButton("Guía rápida")
        help_button.setObjectName("headerAction")
        help_button.setCheckable(True)
        heading.addWidget(help_button)
        layout.addWidget(header)
        info = QLabel(
            "1. Cargue un Excel con las hojas Aulas y Cursos (nombres exactos).\n"
            "2. Revise los cursos y configure aulas o restricciones.\n"
            "3. Genere el horario, revise los grupos pendientes y exporte."
        )
        info.setWordWrap(True)
        info.setObjectName("helpText")
        info.setVisible(False)
        help_button.toggled.connect(info.setVisible)
        layout.addWidget(info)
        self.overview_label = QLabel("Cargue un Excel o agregue cursos y aulas para comenzar.")
        self.overview_label.setObjectName("overview")
        self.overview_label.setWordWrap(True)
        layout.addWidget(self.overview_label)

        file_row = QHBoxLayout()
        lbl = QLabel("Archivo Excel:")
        lbl.setStyleSheet("font-weight: bold;")
        self.excel_path_label = QLabel("Sin archivo seleccionado")
        self.excel_path_label.setWordWrap(True)
        self.excel_path_label.setTextFormat(Qt.TextFormat.PlainText)

        btn_load = self.btn_load = QPushButton("Cargar Excel")
        btn_load.setShortcut("Ctrl+O")
        btn_load.setToolTip(
            "Abrir un archivo Excel (.xlsx) con las hojas:\n"
            "  • Aulas: código, descripción, campus, capacidad\n"
            "  • Cursos: cada fila es un grupo sugerido"
        )
        btn_load.clicked.connect(self._load_excel)

        self.btn_add_classroom = QPushButton("Agregar aula")
        self.btn_add_classroom.setToolTip(
            "Agregar un aula nueva a la sesión actual.\n"
            "Útil para aulas que no están en el Excel pero deben estar disponibles."
        )
        self.btn_add_classroom.clicked.connect(self._add_classroom)

        self.btn_restrictions = QPushButton("Restricciones de aulas")
        self.btn_restrictions.setToolTip(
            "Configurar qué aulas están reservadas exclusivamente para ciertos cursos.\n"
            "Los cursos restringidos SOLO pueden asignarse a su aula designada."
        )
        self.btn_restrictions.clicked.connect(self._configure_restrictions)
        self.btn_restrictions.setEnabled(False)

        file_row.addWidget(lbl)
        file_row.addWidget(self.excel_path_label, 1)
        file_row.addWidget(btn_load)
        file_row.addWidget(self.btn_add_classroom)
        file_row.addWidget(self.btn_restrictions)
        layout.addLayout(file_row)

        return layout

    def _create_actions_section(self) -> QHBoxLayout:
        layout = QHBoxLayout()

        seed_label = QLabel("Semilla:")
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

        self.btn_generate = QPushButton("Generar horario")
        self.btn_generate.setObjectName("primaryAction")
        self.btn_generate.setShortcut("Ctrl+Return")
        self.btn_generate.setToolTip(
            "Ejecutar el algoritmo de programación con los cursos y aulas cargados.\n"
            "El resultado se muestra en la pestaña Horario Generado."
        )
        self.btn_generate.clicked.connect(self._generate_schedule)
        self.btn_generate.setEnabled(False)

        self.btn_export = QPushButton("Exportar completo")
        self.btn_export.setShortcut("Ctrl+S")
        self.btn_export.setToolTip(
            "Guardar el horario generado en formato Excel (.xlsx) o CSV.\n"
            "El Excel incluye una grilla visual por aula."
        )
        self.btn_export.clicked.connect(lambda: self._export_schedule())
        self.btn_export.setEnabled(False)
        self.btn_export_filtered = QPushButton("Exportar filtrado (0)")
        self.btn_export_filtered.setEnabled(False)
        self.btn_export_filtered.clicked.connect(lambda: self._export_schedule(filtered=True))
        self.schedule_viewer.filters_changed.connect(self._update_export_actions)

        layout.addStretch()
        layout.addWidget(seed_label)
        layout.addWidget(self.chk_random_seed)
        layout.addWidget(self.seed_input)
        layout.addWidget(self.btn_generate)
        layout.addWidget(self.btn_export)
        layout.addWidget(self.btn_export_filtered)

        return layout

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _load_excel(self):
        if self._busy:
            return
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
            classroom_course_map = reader.load_course_classroom_map(known_classrooms=known)
            self._loading = True
            self._classroom_course_map = classroom_course_map
            self._classrooms = classrooms

            self.excel_path = file_path
            self.excel_path_label.setText(Path(file_path).name)
            self.excel_path_label.setStyleSheet("color: green;")

            # Load courses into the manager widget
            self.course_manager.load_courses_from_excel(courses)

            # Reset restrictions when a new file is loaded
            self.classroom_restrictions = {}

            self._loading = False
            self._invalidate_schedule()
            self._refresh_overview()
            self.btn_generate.setEnabled(bool(courses and classrooms))
            self.btn_restrictions.setEnabled(bool(self._classroom_course_map))

            self.status_bar.showMessage(
                f"✅ Excel cargado: {Path(file_path).name}  "
                f"({len(classrooms)} aulas, {len(courses)} cursos)"
            )
            self._save_session()

        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 f"Error al cargar archivo Excel:\n{str(e)}")
            self._loading = False
            self.status_bar.showMessage("No se cargó el archivo. La sesión anterior se conserva.")

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
        self._invalidate_schedule()
        self._refresh_overview()
        self.btn_generate.setEnabled(bool(self.course_manager.get_courses()))
        self.status_bar.showMessage(
            f"✅ Aula '{classroom.name}' agregada ({classroom.room_type}, cap={classroom.capacity})"
        )
        self._save_session()

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
            self._invalidate_schedule()
            count = len(self.classroom_restrictions)
            if count:
                self.btn_restrictions.setText(f"🔒 Restricciones ({count})")
                self.status_bar.showMessage(
                    f"✅ {count} aula(s) con restricciones configuradas."
                )
            else:
                self.btn_restrictions.setText("🔒 Aulas con Restricciones")
                self.status_bar.showMessage("Restricciones de aulas eliminadas.")
            self._save_session()

    def _generate_schedule(self):
        if self._busy:
            return
        if not self._classrooms:
            QMessageBox.warning(self, "Advertencia",
                                "Cargue un Excel o agregue al menos un aula primero.")
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
        self._worker.result_ready.connect(self._on_schedule_done)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._worker.error.connect(self._on_schedule_error)

        self._set_busy(True)
        self.status_bar.showMessage("⏳ Generando horario...")
        self._worker.start()

    def _on_schedule_done(self, assignments, groups):

        if assignments:
            self.current_schedule = assignments
            self.current_groups   = groups

            courses = self.course_manager.get_courses()
            time_model = TimeModel.default()
            course_name_map = {c.code: c.name for c in courses if c.name}

            self.schedule_viewer.display_schedule(
                assignments, time_model, groups, course_name_map
            )
            already_showing_results = self.tabs.currentIndex() == 1
            self.tabs.setCurrentIndex(1)
            if already_showing_results:
                self._motion.reveal(self.schedule_viewer)
            self._update_export_actions()

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
            self._refresh_overview()
            self._save_session()
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
        self.status_bar.showMessage("❌ Error al generar horario")
        _InfoDialog(self, "Error", f"Error al generar el horario:\n{message}", warning=True).exec()

    def _update_export_actions(self):
        if not hasattr(self, "btn_export_filtered"):
            return
        count = len(self.schedule_viewer.filtered_assignments())
        ready = not self._busy and bool(self.current_schedule)
        self.btn_export.setEnabled(ready)
        self.btn_export_filtered.setText(f"Exportar filtrado ({count})")
        self.btn_export_filtered.setEnabled(ready and count > 0)
        self.btn_export_filtered.setToolTip(
            f"Exportar {count} sesiones asignadas que coinciden con Buscar, Aula, Día y Estado.\n"
            "La pestaña activa y el selector del aula de la cuadrícula no cambian este conjunto."
        )

    def _export_schedule(self, filtered=False):
        if self._busy:
            return
        if not self.current_schedule:
            QMessageBox.warning(self, "Advertencia", "No hay horario para exportar.")
            return
        assignments = (self.schedule_viewer.filtered_assignments() if filtered
                       else dict(self.current_schedule))
        if not assignments:
            QMessageBox.information(self, "Sin coincidencias",
                                    "No hay sesiones asignadas con estos filtros. Cambie o restablezca los filtros.")
            return
        scope = "filtrado" if filtered else "completo"
        count = len(assignments)
        file_path, selected_format = QFileDialog.getSaveFileName(
            self, f"Guardar horario {scope} · {count} sesiones",
            "horario_filtrado.xlsx" if filtered else "horario.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return
        if not Path(file_path).suffix:
            file_path += ".csv" if selected_format.startswith("CSV") else ".xlsx"

        try:
            time_model = TimeModel.default()
            exporter = ScheduleExporter(time_model)
            courses = self.course_manager.get_courses()
            course_name_map = {c.code: c.name for c in courses if c.name}
            if file_path.lower().endswith(".csv"):
                exporter.to_csv(assignments, file_path, groups=self.current_groups,
                                course_name_by_code=course_name_map)
            else:
                exporter.to_excel(assignments, file_path, groups=self.current_groups,
                                  course_name_by_code=course_name_map, include_grid=True)
            self.status_bar.showMessage(f"Horario {scope}: {count} sesiones exportadas a {Path(file_path).name}")
            _InfoDialog(self, "Éxito", f"Horario {scope}: {count} sesiones exportadas a:\n{file_path}").exec()
        except Exception as e:
            _InfoDialog(self, "Error", f"Error al exportar:\n{str(e)}", warning=True).exec()

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------

    def _save_session(self):
        if self._loading:
            return
        try:
            seed = None if self.chk_random_seed.isChecked() else self.seed_input.value()
            self._repo.save_session(
                excel_path=self.excel_path,
                seed=seed,
                classrooms=self._classrooms,
                courses=self.course_manager.get_courses(),
                restrictions=self.classroom_restrictions,
                assignments=self.current_schedule,
            )
        except Exception as error:
            self.status_bar.showMessage(f"No se pudo guardar la sesión: {error}")

    def _restore_session_if_exists(self):
        if not self._repo.has_session():
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Sesión anterior")
        dlg.setModal(True)
        dlg.setMinimumWidth(500)
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        hdr = QLabel("  💾  Sesión anterior encontrada")
        hdr.setStyleSheet(
            "background-color: #1967D2; color: #FFFFFF; "
            "font-size: 12pt; font-weight: bold; padding: 14px 20px;"
        )
        outer.addWidget(hdr)
        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(28, 20, 28, 20)
        bl.setSpacing(20)
        lbl = QLabel("Se encontró una sesión guardada.\n¿Deseas restaurarla?")
        lbl.setStyleSheet("font-size: 11pt;")
        lbl.setMinimumWidth(440)
        bl.addWidget(lbl)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes | QDialogButtonBox.StandardButton.No
        )
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        bl.addWidget(btns)
        outer.addWidget(body)
        dlg.setLayout(outer)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return  # user said No — app starts normally with empty state
        try:
            data = self._repo.load_session()
            if not data:
                return

            self._classrooms = data["classrooms"]
            self.classroom_restrictions = data["restrictions"]

            if data["excel_path"] and Path(data["excel_path"]).exists():
                self.excel_path = data["excel_path"]
                self.excel_path_label.setText(Path(data["excel_path"]).name)
                self.excel_path_label.setStyleSheet("color: green;")
                # Reload classroom-course map from Excel for restrictions dialog
                try:
                    from ..infrastructure.excel_reader import ExcelReader as _ER
                    r = _ER(data["excel_path"])
                    self._classroom_course_map = r.load_course_classroom_map(
                        known_classrooms=set(self._classrooms.keys())
                    )
                except Exception:
                    pass

            self._loading = True
            self.course_manager.load_courses_from_excel(data["courses"])
            self._loading = False

            self.chk_random_seed.setChecked(data["seed"] is None)
            if data["seed"] is not None:
                self.seed_input.setValue(data["seed"])

            count = len(self.classroom_restrictions)
            if count:
                self.btn_restrictions.setText(f"🔒 Restricciones ({count})")
            self.btn_restrictions.setEnabled(bool(self._classroom_course_map))
            self.btn_generate.setEnabled(bool(data["courses"]))

            if data["assignments"]:
                self.current_schedule = data["assignments"]
                time_model = TimeModel.default()
                course_name_map = {c.code: c.name for c in data["courses"] if c.name}
                # Regenerate groups so the viewer has full group info
                groups = []
                for c in data["courses"]:
                    groups.extend(c.generate_groups())
                # Re-attach assignments to groups
                for g in groups:
                    if g.group_id in data["assignments"]:
                        g.assignment = data["assignments"][g.group_id]
                self.current_groups = groups
                self.schedule_viewer.display_schedule(
                    data["assignments"], time_model, groups, course_name_map
                )
                self._update_export_actions()

            self._refresh_overview()
            self.status_bar.showMessage("✅ Sesión restaurada correctamente.")
        except Exception as e:
            self._loading = False
            self.status_bar.showMessage(f"⚠️ No se pudo restaurar la sesión: {e}")

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
                    g.assignment = None

        self._update_export_actions()
        self._refresh_overview()
        self._save_session()

    def _on_schedule_cleared(self):
        self.current_schedule = None
        self.current_groups = None
        self._update_export_actions()
        self._refresh_overview()
        self.status_bar.showMessage("Horario eliminado.")
        self._save_session()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _refresh_overview(self):
        courses = self.course_manager.get_courses()
        groups = sum(len(course.generate_groups()) for course in courses)
        text = f"{len(courses)} cursos  ·  {groups} sesiones  ·  {len(self._classrooms)} aulas"
        if self.current_schedule:
            text += f"  ·  {len(self.current_schedule)}/{groups} sesiones asignadas"
        elif courses:
            text += "  ·  Listo para generar"
        else:
            text += "  ·  Cargue un Excel para comenzar"
        self.overview_label.setText(text)

    def _invalidate_schedule(self):
        self.current_schedule = None
        self.current_groups = None
        self.schedule_viewer._clear()
        self._update_export_actions()

    def _on_inputs_changed(self):
        if self._loading:
            return
        self._invalidate_schedule()
        self._refresh_overview()
        self.btn_generate.setEnabled(bool(self._classrooms and self.course_manager.get_courses()))
        self.status_bar.showMessage("Datos actualizados. Genere un nuevo horario para exportar.")
        self._save_session()

    def _set_reduced_motion(self, reduced):
        self._motion.set_reduced(reduced)
        update_busy_indicator(self._progress, self._busy, self._motion.reduced)

    def _set_busy(self, busy):
        self._busy = busy
        for control in (self.btn_load, self.btn_add_classroom, self.course_manager,
                        self.schedule_viewer, self.chk_random_seed):
            control.setEnabled(not busy)
        self.seed_input.setEnabled(not busy and not self.chk_random_seed.isChecked())
        self.btn_restrictions.setEnabled(not busy and bool(self._classroom_course_map))
        self.btn_generate.setEnabled(not busy and bool(self._classrooms and self.course_manager.get_courses()))
        self.btn_generate.setText("Generando…" if busy else "Generar horario")
        self._update_export_actions()
        update_busy_indicator(self._progress, busy, self._motion.reduced)

    def closeEvent(self, event):
        if self._worker is not None and self._worker.isRunning():
            self.status_bar.showMessage("Espere a que termine la generación antes de cerrar.")
            event.ignore()
            return
        self._motion.finish()
        self._save_session()
        event.accept()

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
