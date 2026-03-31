# src/gui/schedule_viewer_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QLabel, QHeaderView, QTabWidget, QPushButton,
                             QMessageBox, QComboBox, QHBoxLayout, QDialog,
                             QDialogButtonBox, QGridLayout, QFrame, QMenu,
                             QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QAction

from ..scheduling.time_model import TimeModel

_DAY_ORDER = {d: i for i, d in enumerate(
    ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
)}


class _SortableItem(QTableWidgetItem):
    """QTableWidgetItem that sorts by a numeric key instead of display text."""
    def __init__(self, text: str, sort_key):
        super().__init__(text)
        self._sort_key = sort_key

    def __lt__(self, other):
        if isinstance(other, _SortableItem):
            return self._sort_key < other._sort_key
        return super().__lt__(other)


class ScheduleViewerWidget(QWidget):

    # Emitted when user requests to edit a course by code
    edit_course_requested  = pyqtSignal(str)   # course_code
    # Emitted when user removes a group from the schedule
    group_removed          = pyqtSignal(str)   # group_id
    _COLOR_PALETTE = [
        QColor(76, 175, 80),   QColor(33, 150, 243),  QColor(255, 152, 0),
        QColor(156, 39, 176),  QColor(244, 67, 54),   QColor(0, 150, 136),
        QColor(233, 30, 99),   QColor(63, 81, 181),   QColor(255, 87, 34),
        QColor(103, 58, 183),
    ]

    def __init__(self):
        super().__init__()
        self._classroom_colors: dict[str, QColor] = {}
        self._course_colors: dict[str, QColor] = {}
        self._duration_map: dict[str, int] = {}       # group_id → duration_min
        self._name_map: dict[str, str] = {}           # group_id → course_name
        self._classroom_assignments: dict[str, list] = {}
        self._assignments: dict = {}                  # full assignments dict
        self._gid_by_list_row: dict[int, str] = {}    # list table row → group_id
        self._gid_by_cls_row: dict[int, str] = {}     # classroom table row → group_id
        self._time_model: TimeModel | None = None
        self.summary_data: dict | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title = QLabel("Horario Generado")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        btn_summary = QPushButton("📊 Ver Resumen")
        btn_summary.setToolTip("Ver totales: grupos asignados, aulas utilizadas y cursos programados")
        btn_summary.clicked.connect(self._show_summary)
        btn_summary.setMaximumWidth(130)
        btn_summary.setStyleSheet(
            "QPushButton { background-color: #1967D2; color: white; "
            "padding: 6px 12px; border-radius: 3px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1565C0; }"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_summary)
        layout.addLayout(header_layout)

        self.tabs = QTabWidget()

        # Tab 1 — detailed list
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)

        search_row = QHBoxLayout()
        self._list_search = QLineEdit()
        self._list_search.setPlaceholderText("🔍  Buscar por código o nombre de curso...")
        self._list_search.textChanged.connect(self._filter_list)
        sort_hint = QLabel("Clic en encabezado para ordenar  •  Clic derecho o botones para editar/eliminar")
        sort_hint.setStyleSheet("color: #555; font-style: italic; padding: 2px 4px;")
        search_row.addWidget(self._list_search, 1)
        search_row.addWidget(sort_hint)
        list_layout.addLayout(search_row)
        self.list_table = QTableWidget()
        self.list_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(self.list_table, pos, self._gid_by_list_row)
        )
        list_btn_row = QHBoxLayout()
        btn_edit_list = QPushButton("✏️ Editar Curso")
        btn_edit_list.setToolTip("Editar el curso de la fila seleccionada")
        btn_edit_list.clicked.connect(lambda: self._action_edit(self.list_table, self._gid_by_list_row))
        btn_remove_list = QPushButton("🗑️ Eliminar del Horario")
        btn_remove_list.setToolTip("Quitar este grupo del horario generado")
        btn_remove_list.clicked.connect(lambda: self._action_remove(self.list_table, self._gid_by_list_row))
        list_btn_row.addWidget(btn_edit_list)
        list_btn_row.addWidget(btn_remove_list)
        list_btn_row.addStretch()
        list_layout.addWidget(sort_hint)
        list_layout.addWidget(self.list_table)
        list_layout.addLayout(list_btn_row)
        list_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(list_widget, "📋 Lista Detallada")


        # Tab 2 — grid per classroom
        grid_widget = QWidget()
        grid_layout = QVBoxLayout(grid_widget)
        sel_layout = QHBoxLayout()
        sel_layout.addWidget(QLabel("Aula:"))
        self.classroom_selector = QComboBox()
        self.classroom_selector.setMinimumWidth(220)
        self.classroom_selector.setToolTip("Seleccionar el aula a visualizar en la cuadrícula")
        self.classroom_selector.currentTextChanged.connect(self._render_grid)
        sel_layout.addWidget(self.classroom_selector)
        sel_layout.addStretch()
        self.grid_table = QTableWidget()
        grid_layout.addLayout(sel_layout)
        grid_layout.addWidget(self.grid_table)
        self.tabs.addTab(grid_widget, "📅 Vista de Cuadrícula")

        # Tab 3 — by classroom
        cls_widget = QWidget()
        cls_layout = QVBoxLayout(cls_widget)

        cls_search_row = QHBoxLayout()
        self._cls_search = QLineEdit()
        self._cls_search.setPlaceholderText("🔍  Buscar por aula o grupo...")
        self._cls_search.textChanged.connect(self._filter_cls)
        sort_hint2 = QLabel("Clic en encabezado para ordenar  •  Clic derecho o botones para editar/eliminar")
        sort_hint2.setStyleSheet("color: #555; font-style: italic; padding: 2px 4px;")
        cls_search_row.addWidget(self._cls_search, 1)
        cls_search_row.addWidget(sort_hint2)
        cls_layout.addLayout(cls_search_row)
        self.classroom_table = QTableWidget()
        self.classroom_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.classroom_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(self.classroom_table, pos, self._gid_by_cls_row)
        )
        cls_btn_row = QHBoxLayout()
        btn_edit_cls = QPushButton("✏️ Editar Curso")
        btn_edit_cls.setToolTip("Editar el curso de la fila seleccionada")
        btn_edit_cls.clicked.connect(lambda: self._action_edit(self.classroom_table, self._gid_by_cls_row))
        btn_remove_cls = QPushButton("🗑️ Eliminar del Horario")
        btn_remove_cls.setToolTip("Quitar este grupo del horario generado")
        btn_remove_cls.clicked.connect(lambda: self._action_remove(self.classroom_table, self._gid_by_cls_row))
        cls_btn_row.addWidget(btn_edit_cls)
        cls_btn_row.addWidget(btn_remove_cls)
        cls_btn_row.addStretch()
        cls_layout.addWidget(sort_hint2)
        cls_layout.addWidget(self.classroom_table)
        cls_layout.addLayout(cls_btn_row)
        cls_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(cls_widget, "🏫 Por Aula")

        layout.addWidget(self.tabs, 1)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------

    def _clear(self):
        self.list_table.clear()
        self.list_table.setRowCount(0)
        self.grid_table.clear()
        self.grid_table.setRowCount(0)
        self.classroom_table.clear()
        self.classroom_table.setRowCount(0)
        self.classroom_selector.blockSignals(True)
        self.classroom_selector.clear()
        self.classroom_selector.blockSignals(False)
        self._classroom_colors.clear()
        self._course_colors.clear()
        self._duration_map.clear()
        self._name_map.clear()
        self._classroom_assignments.clear()
        self._assignments.clear()
        self._gid_by_list_row.clear()
        self._gid_by_cls_row.clear()
        self.summary_data = None
        self._list_search.clear()
        self._cls_search.clear()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def display_schedule(self, assignments: dict, time_model: TimeModel,
                         groups=None, course_name_by_code: dict = None):
        self._clear()
        if not assignments:
            return

        self._assignments = dict(assignments)
        self._time_model = time_model
        course_name_by_code = course_name_by_code or {}

        # Build helper maps
        self._duration_map = {}
        self._name_map = {}
        if groups:
            for g in groups:
                self._duration_map[g.group_id] = g.duration_min
                if g.course_name:
                    self._name_map[g.group_id] = g.course_name

        for gid in assignments:
            if gid not in self._name_map:
                code = gid.rsplit('-G', 1)[0]
                if code in course_name_by_code and course_name_by_code[code]:
                    self._name_map[gid] = course_name_by_code[code]

        # Course color map (one color per unique course code)
        course_codes = sorted(set(gid.rsplit('-G', 1)[0] for gid in assignments))
        self._course_colors = {
            code: self._COLOR_PALETTE[i % len(self._COLOR_PALETTE)]
            for i, code in enumerate(course_codes)
        }

        # Classroom color map (kept for grid selector label)
        classrooms = sorted(set(v[0] for v in assignments.values()))
        self._classroom_colors = {
            c: self._COLOR_PALETTE[i % len(self._COLOR_PALETTE)]
            for i, c in enumerate(classrooms)
        }

        # Group assignments by classroom for grid view
        self._classroom_assignments = {}
        for gid, (cls, day, start, end) in assignments.items():
            self._classroom_assignments.setdefault(cls, []).append((gid, day, start, end))

        unassigned_groups = [g for g in (groups or []) if not g.is_assigned()]

        self._display_list(assignments, time_model, unassigned_groups, course_name_by_code)
        self._display_grid_selector(classrooms)
        self._display_classroom_view(assignments, time_model)
        self._update_summary(assignments, unassigned_groups)

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    def _display_list(self, assignments: dict, tm: TimeModel,
                       unassigned_groups: list = None, course_name_by_code: dict = None):
        course_name_by_code = course_name_by_code or {}
        unassigned_groups = unassigned_groups or []

        total_rows = len(assignments) + len(unassigned_groups)
        self.list_table.clear()
        self.list_table.setRowCount(total_rows)
        self.list_table.setColumnCount(7)
        self.list_table.setHorizontalHeaderLabels([
            "Código Curso", "Nombre", "Grupo", "Aula", "Día", "Hora Inicio", "Hora Fin"
        ])

        red_bg = QColor(255, 205, 210)
        red_fg = QColor(183, 28, 28)

        self.list_table.setSortingEnabled(False)

        for row, (gid, (cls, day, start_min, end_min)) in enumerate(sorted(assignments.items())):
            code = gid.rsplit('-G', 1)[0]
            display_gid = gid.split('-P', 1)[0]
            name = self._name_map.get(gid) or course_name_by_code.get(code, "")
            day_name = tm.to_day_name(day)
            values = [code, name, display_gid, cls, day_name,
                      TimeModel.minutes_to_hhmm(start_min),
                      TimeModel.minutes_to_hhmm(end_min)]
            for col, val in enumerate(values):
                if col == 4:  # Día
                    item = _SortableItem(val, _DAY_ORDER.get(val, 99))
                elif col in (5, 6):  # Hora Inicio / Hora Fin
                    item = _SortableItem(val, start_min if col == 5 else end_min)
                else:
                    item = QTableWidgetItem(str(val))
                self.list_table.setItem(row, col, item)
            self._gid_by_list_row[row] = gid

        for i, g in enumerate(sorted(unassigned_groups, key=lambda g: g.group_id)):
            row = len(assignments) + i
            code = g.course_code or g.group_id.rsplit('-G', 1)[0]
            name = g.course_name or course_name_by_code.get(code, "")
            display_gid = g.group_id.split('-P', 1)[0]
            for col, val in enumerate([code, name, display_gid,
                                        "⚠ Sin asignar", "-", "-", "-"]):
                item = QTableWidgetItem(str(val))
                item.setBackground(red_bg)
                item.setForeground(red_fg)
                self.list_table.setItem(row, col, item)

        self.list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.list_table.setSortingEnabled(True)

    # ------------------------------------------------------------------
    # Grid view
    # ------------------------------------------------------------------

    # Grid resolution: 30-minute slots from 07:00 to 21:00
    _GRID_STEP   = 30          # minutes per row
    _GRID_START  = 7 * 60      # 420
    _GRID_END    = 21 * 60     # 1260
    _GRID_ROWS   = (_GRID_END - _GRID_START) // _GRID_STEP  # 28
    _ROW_HEIGHT  = 40          # pixels per 30-min slot

    def _min_to_row(self, minutes: int) -> int:
        """Convert absolute minutes to grid row index."""
        return (minutes - self._GRID_START) // self._GRID_STEP

    def _display_grid_selector(self, classrooms: list[str]):
        current = self.classroom_selector.currentText()
        self.classroom_selector.blockSignals(True)
        self.classroom_selector.clear()
        self.classroom_selector.addItems(classrooms)
        self.classroom_selector.blockSignals(False)

        selected = current if current in classrooms else (classrooms[0] if classrooms else "")
        self.classroom_selector.setCurrentText(selected)
        self._render_grid(selected)

    def _render_grid(self, classroom: str):
        if not classroom or not self._time_model:
            return

        tm   = self._time_model
        days = tm.days
        n_rows = self._GRID_ROWS
        n_cols = len(days) + 1

        # Reset spans before rebuilding to avoid overlap errors
        self.grid_table.clearSpans()
        self.grid_table.clear()
        self.grid_table.setRowCount(n_rows)
        self.grid_table.setColumnCount(n_cols)
        self.grid_table.setHorizontalHeaderLabels(["Hora"] + days)

        color_header = QColor(25, 103, 210)
        color_hour   = QColor(240, 240, 240)
        color_empty  = QColor(250, 250, 250)
        black        = QColor(0, 0, 0)
        white_text   = QColor(255, 255, 255)

        # --- Hour labels ---
        for row in range(n_rows):
            t = self._GRID_START + row * self._GRID_STEP
            item = QTableWidgetItem(TimeModel.minutes_to_hhmm(t))
            item.setBackground(color_hour)
            item.setForeground(black)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            item.setFont(self._font(bold=True, size=8))
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.grid_table.setItem(row, 0, item)

        # --- Empty cells ---
        for row in range(n_rows):
            for col in range(1, n_cols):
                item = QTableWidgetItem("")
                item.setBackground(color_empty)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.grid_table.setItem(row, col, item)

        # --- Course blocks ---
        # Track occupied (row, col) ranges to avoid span overlaps
        occupied: dict[tuple[int, int], int] = {}  # (row, col) -> last occupied row

        entries = self._classroom_assignments.get(classroom, [])
        for gid, day, start_min, end_min in sorted(entries, key=lambda e: e[2]):
            day_name = tm.to_day_name(day)
            if day_name not in days:
                continue
            col = days.index(day_name) + 1

            start_row = self._min_to_row(start_min)
            duration  = end_min - start_min
            span      = max(1, (duration + self._GRID_STEP - 1) // self._GRID_STEP)

            if start_row < 0 or start_row >= n_rows:
                continue
            span = min(span, n_rows - start_row)

            # Shrink span if it would overlap an already-placed block
            for r in range(start_row, start_row + span):
                if (r, col) in occupied:
                    span = r - start_row
                    break
            if span < 1:
                continue

            # Mark rows as occupied
            for r in range(start_row, start_row + span):
                occupied[(r, col)] = 1

            code      = gid.rsplit('-G', 1)[0]
            group_num = gid.split('-P', 1)[0].rsplit('-G', 1)[1]
            name      = self._name_map.get(gid, "")
            time_lbl  = f"{TimeModel.minutes_to_hhmm(start_min)}–{TimeModel.minutes_to_hhmm(end_min)}"
            cell_text = f"{code}\n{name}\nG{group_num}\n{time_lbl}" if name else f"{code}\nG{group_num}\n{time_lbl}"

            course_color = self._course_colors.get(code, self._COLOR_PALETTE[0])
            item = QTableWidgetItem(cell_text)
            item.setBackground(course_color)
            item.setForeground(black)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            item.setFont(self._font(size=8))
            item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.grid_table.setItem(start_row, col, item)
            if span > 1:
                self.grid_table.setSpan(start_row, col, span, 1)

        # --- Sizing ---
        hdr = self.grid_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.grid_table.setColumnWidth(0, 55)
        for c in range(1, n_cols):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeMode.Stretch)

        for i in range(self.grid_table.columnCount()):
            h = self.grid_table.horizontalHeaderItem(i)
            if h:
                h.setBackground(color_header)
                h.setForeground(white_text)
                h.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                h.setFont(self._font(bold=True))

        self.grid_table.verticalHeader().setVisible(False)
        for row in range(n_rows):
            self.grid_table.setRowHeight(row, self._ROW_HEIGHT)

    # ------------------------------------------------------------------
    # Classroom view
    # ------------------------------------------------------------------

    def _display_classroom_view(self, assignments: dict, tm: TimeModel):
        rows_data = []
        for gid, (cls, day, start_min, end_min) in assignments.items():
            rows_data.append((cls, gid, tm.to_day_name(day), start_min, end_min))
        rows_data.sort(key=lambda x: (x[0], x[2], x[3]))

        self.classroom_table.clear()
        self.classroom_table.setRowCount(len(rows_data))
        self.classroom_table.setColumnCount(5)
        self.classroom_table.setHorizontalHeaderLabels([
            "Aula", "Grupo", "Día", "Hora Inicio", "Hora Fin"
        ])
        self.classroom_table.setSortingEnabled(False)

        for row, (cls, gid, day_name, start_min, end_min) in enumerate(rows_data):
            self.classroom_table.setItem(row, 0, QTableWidgetItem(cls))
            self.classroom_table.setItem(row, 1, QTableWidgetItem(gid.split('-P', 1)[0]))
            self.classroom_table.setItem(row, 2, _SortableItem(day_name, _DAY_ORDER.get(day_name, 99)))
            self.classroom_table.setItem(row, 3, _SortableItem(TimeModel.minutes_to_hhmm(start_min), start_min))
            self.classroom_table.setItem(row, 4, _SortableItem(TimeModel.minutes_to_hhmm(end_min), end_min))
            self._gid_by_cls_row[row] = gid

        self.classroom_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.classroom_table.setSortingEnabled(True)

    # ------------------------------------------------------------------
    # Search / filter
    # ------------------------------------------------------------------

    def _filter_list(self, text: str):
        text = text.strip().lower()
        for row in range(self.list_table.rowCount()):
            match = False
            for col in (0, 1):  # code, name
                item = self.list_table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.list_table.setRowHidden(row, not match if text else False)

    def _filter_cls(self, text: str):
        text = text.strip().lower()
        for row in range(self.classroom_table.rowCount()):
            aula  = self.classroom_table.item(row, 0)
            grupo = self.classroom_table.item(row, 1)
            match = (
                (aula  and text in aula.text().lower()) or
                (grupo and text in grupo.text().lower())
            )
            self.classroom_table.setRowHidden(row, not match if text else False)

    # ------------------------------------------------------------------
    # Context menu (edit / remove)
    # ------------------------------------------------------------------

    def _show_context_menu(self, table: QTableWidget, pos, gid_map: dict):
        row = table.rowAt(pos.y())
        if row < 0:
            return
        gid = gid_map.get(row)
        if not gid:
            return
        code = gid.rsplit('-G', 1)[0]

        menu = QMenu(self)
        act_edit   = QAction(f"✏️  Editar curso {code}", self)
        act_remove = QAction(f"🗑️  Eliminar grupo del horario", self)
        menu.addAction(act_edit)
        menu.addSeparator()
        menu.addAction(act_remove)

        act_edit.triggered.connect(lambda: self.edit_course_requested.emit(code))
        act_remove.triggered.connect(lambda: self._remove_group(gid))
        menu.exec(table.viewport().mapToGlobal(pos))

    def _action_edit(self, table: QTableWidget, gid_map: dict):
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Selecciona una fila primero.")
            return
        gid = gid_map.get(row)
        if gid:
            self.edit_course_requested.emit(gid.rsplit('-G', 1)[0])

    def _action_remove(self, table: QTableWidget, gid_map: dict):
        row = table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Info", "Selecciona una fila primero.")
            return
        gid = gid_map.get(row)
        if gid:
            self._remove_group(gid)

    def _remove_group(self, gid: str):
        if gid not in self._assignments:
            return
        cls_name = self._assignments[gid][0]
        del self._assignments[gid]
        self.group_removed.emit(gid)

        # Update classroom assignments map
        if cls_name in self._classroom_assignments:
            self._classroom_assignments[cls_name] = [
                e for e in self._classroom_assignments[cls_name] if e[0] != gid
            ]

        # Refresh all views
        if self._time_model:
            self._display_list(self._assignments, self._time_model, [], {})
            self._display_classroom_view(self._assignments, self._time_model)
            self._render_grid(self.classroom_selector.currentText())
            self._update_summary(self._assignments, [])

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _update_summary(self, assignments: dict, unassigned_groups: list = None):
        unassigned = unassigned_groups or []
        # Per-classroom load
        cls_load: dict[str, int] = {}
        for cls, _, _, _ in assignments.values():
            cls_load[cls] = cls_load.get(cls, 0) + 1

        # Per-day load
        day_load: dict[str, int] = {}
        if self._time_model:
            for _, day, _, _ in assignments.values():
                name = self._time_model.to_day_name(day)
                day_load[name] = day_load.get(name, 0) + 1

        self.summary_data = {
            "total":       len(assignments),
            "unassigned":  len(unassigned),
            "classrooms":  len(cls_load),
            "courses":     len(set(gid.rsplit('-G', 1)[0] for gid in assignments)),
            "cls_load":    cls_load,
            "day_load":    day_load,
            "unassigned_list": [(g.course_code or g.group_id.rsplit('-G',1)[0],
                                  g.course_name or "",
                                  g.group_id.split('-P',1)[0])
                                 for g in sorted(unassigned, key=lambda g: g.group_id)],
        }

    def _show_summary(self):
        if not self.summary_data:
            QMessageBox.information(self, "Info", "No hay horario generado aún.")
            return
        d = self.summary_data
        dlg = SummaryDialog(self, d)
        dlg.exec()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _font(self, bold: bool = False, size: int = 10) -> QFont:
        f = QFont("Arial", size)
        f.setBold(bold)
        return f


class SummaryDialog(QDialog):

    def __init__(self, parent, data: dict):
        super().__init__(parent)
        self.setWindowTitle("Resumen del Horario")
        self.setModal(True)
        self.resize(520, 480)
        self._data = data
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # --- KPI cards ---
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(8)
        assigned   = self._data["total"]
        unassigned = self._data["unassigned"]
        total      = assigned + unassigned
        pct        = int(assigned / total * 100) if total else 0

        for label, value, color in [
            ("Grupos asignados",  f"{assigned} / {total}  ({pct}%)", "#2E7D32"),
            ("Sin asignar",       str(unassigned),                   "#B71C1C" if unassigned else "#2E7D32"),
            ("Aulas utilizadas",  str(self._data["classrooms"]),     "#1565C0"),
            ("Cursos programados",str(self._data["courses"]),        "#6A1B9A"),
        ]:
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: {color}; border-radius: 6px; padding: 4px; }}"
            )
            cl = QVBoxLayout(card)
            cl.setSpacing(2)
            vl = QLabel(value)
            vl.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
            vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ll = QLabel(label)
            ll.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 10px;")
            ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(vl)
            cl.addWidget(ll)
            kpi_row.addWidget(card)
        layout.addLayout(kpi_row)

        # --- Load by day ---
        if self._data.get("day_load"):
            layout.addWidget(self._section_label("Grupos por día"))
            day_table = self._make_table(["Día", "Grupos asignados"],
                                         sorted(self._data["day_load"].items()))
            layout.addWidget(day_table)

        # --- Load by classroom ---
        if self._data.get("cls_load"):
            layout.addWidget(self._section_label("Grupos por aula"))
            cls_table = self._make_table(
                ["Aula", "Grupos asignados"],
                sorted(self._data["cls_load"].items(), key=lambda x: -x[1])
            )
            layout.addWidget(cls_table)

        # --- Unassigned groups ---
        if self._data.get("unassigned_list"):
            lbl = self._section_label("⚠ Grupos sin asignar (ver Lista Detallada en rojo)")
            lbl.setStyleSheet("font-weight: bold; color: #B71C1C;")
            layout.addWidget(lbl)
            ua_table = self._make_table(
                ["Código", "Nombre", "Grupo"],
                self._data["unassigned_list"]
            )
            layout.addWidget(ua_table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; font-size: 11px;")
        return lbl

    def _make_table(self, headers: list, rows: list) -> QTableWidget:
        t = QTableWidget(len(rows), len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setMaximumHeight(min(len(rows) * 28 + 30, 160))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                t.setItem(r, c, QTableWidgetItem(str(val)))
        return t
