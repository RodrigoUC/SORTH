# src/gui/schedule_viewer_widget.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QLabel, QHeaderView, QTabWidget, QPushButton,
                             QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from typing import Dict, Tuple

from ..scheduling.time_model import TimeModel


class ScheduleViewerWidget(QWidget):
    """Widget for viewing the generated schedule."""

    def __init__(self):
        super().__init__()
        self._classroom_colors = {}
        self.init_ui()

    def init_ui(self):
        """Initialize the widget UI."""
        layout = QVBoxLayout()

        # Title with Summary button
        title_layout = QVBoxLayout()
        
        title = QLabel("Horario Generado")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0px;")
        title_layout.addWidget(title)
        
        # Summary button
        btn_summary = QPushButton("📊 Ver Resumen")
        btn_summary.clicked.connect(self._show_summary_popup)
        btn_summary.setMaximumWidth(120)
        btn_summary.setStyleSheet("""
            QPushButton {
                background-color: #1967D2;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        title_layout.addWidget(btn_summary)
        
        layout.addLayout(title_layout)

        # Tab widget for different views
        self.tabs = QTabWidget()
        
        # List view
        self.list_table = QTableWidget()
        self.tabs.addTab(self.list_table, "📋 Lista Detallada")
        
        # Grid view (full width without legend)
        self.grid_table = QTableWidget()
        self.tabs.addTab(self.grid_table, "📅 Vista de Cuadrícula")
        
        # Classroom view
        self.classroom_table = QTableWidget()
        self.tabs.addTab(self.classroom_table, "🏫 Por Aula")
        
        layout.addWidget(self.tabs, 1)

        self.setLayout(layout)

        # Store summary data
        self.summary_data = None

        # Show empty state initially
        self._show_empty_state()

    def _show_empty_state(self):
        """Show empty state when no schedule is loaded."""
        pass

    def display_schedule(self, assignments: Dict[str, Tuple[str, int, int]], 
                        time_model: TimeModel):
        """Display the generated schedule."""
        if not assignments:
            self._show_empty_state()
            return

        # Display list view
        self._display_list_view(assignments, time_model)
        
        # Display grid view
        self._display_grid_view(assignments, time_model)
        
        # Display classroom view
        self._display_classroom_view(assignments, time_model)
        
        # Update summary (for the popup)
        self._update_summary(assignments)

    def _display_list_view(self, assignments: Dict[str, Tuple[str, int, int]], 
                           time_model: TimeModel):
        """Display the list view of assignments."""
        self.list_table.clear()
        self.list_table.setRowCount(len(assignments))
        self.list_table.setColumnCount(6)
        self.list_table.setHorizontalHeaderLabels([
            "Código Curso", "Grupo", "Aula", "Día", "Hora Inicio", "Bloque"
        ])
        
        row = 0
        for group_id, (classroom, day_i, block_i) in sorted(assignments.items()):
            day_name, hour = time_model.to_external(day_i, block_i)
            course_code = group_id.rsplit('-G', 1)[0]
            
            self.list_table.setItem(row, 0, QTableWidgetItem(course_code))
            self.list_table.setItem(row, 1, QTableWidgetItem(group_id))
            self.list_table.setItem(row, 2, QTableWidgetItem(classroom))
            self.list_table.setItem(row, 3, QTableWidgetItem(day_name))
            self.list_table.setItem(row, 4, QTableWidgetItem(f"{hour}:00"))
            self.list_table.setItem(row, 5, QTableWidgetItem(str(block_i + 1)))
            
            row += 1
        
        self.list_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _display_grid_view(self, assignments: Dict[str, Tuple[str, int, int]], 
                          time_model: TimeModel):
        """Display the grid/timetable view."""
        days = time_model.days
        hours = sorted(time_model.hours)
        
        self.grid_table.clear()
        self.grid_table.setRowCount(len(hours))
        self.grid_table.setColumnCount(len(days) + 1)
        
        # Set headers
        headers = ["Hora"] + days
        self.grid_table.setHorizontalHeaderLabels(headers)
        
        # Initialize grid
        grid = {}
        for hour in hours:
            grid[hour] = {day: [] for day in days}
        
        # Fill grid with assignments
        for group_id, (classroom, day_i, block_i) in assignments.items():
            day_name, hour = time_model.to_external(day_i, block_i)
            course_code = group_id.rsplit('-G', 1)[0]
            group_num = group_id.rsplit('-G', 1)[1]
            cell_text = f"{course_code}-G{group_num}\n({classroom})"
            grid[hour][day_name].append((cell_text, classroom, course_code))
        
        # Color palette - different colors for each classroom
        self._setup_classroom_colors(assignments)
        
        # Color definitions
        color_header = QColor(25, 103, 210)  # Dark blue
        color_hour = QColor(240, 240, 240)   # Light gray
        text_color_header = QColor(255, 255, 255)  # White
        text_color_dark = QColor(0, 0, 0)  # Black
        
        # Populate table
        for row_idx, hour in enumerate(hours):
            # Hour column
            hour_item = QTableWidgetItem(f"{hour}:00")
            hour_item.setBackground(color_hour)
            hour_item.setForeground(text_color_dark)
            hour_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            hour_item.setFont(self._get_font(bold=True))
            self.grid_table.setItem(row_idx, 0, hour_item)
            
            # Day columns
            for col_idx, day in enumerate(days):
                assignments_list = grid[hour][day]
                
                if assignments_list:
                    # Display all assignments in this cell
                    assignment_text = '\n---\n'.join([cell[0] for cell in assignments_list])
                    item = QTableWidgetItem(assignment_text)
                    
                    # Get color from first classroom in the cell
                    classroom = assignments_list[0][1]
                    cell_color = self._classroom_colors.get(classroom, QColor(76, 175, 80))
                    
                    item.setBackground(cell_color)
                    item.setForeground(text_color_dark)
                    item.setFont(self._get_font(bold=False, size=9))
                else:
                    item = QTableWidgetItem("")
                    item.setBackground(QColor(255, 255, 255))  # White
                    item.setForeground(text_color_dark)
                
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.grid_table.setItem(row_idx, col_idx + 1, item)
        
        # Set header formatting
        header = self.grid_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for i in range(len(headers)):
            header_item = self.grid_table.horizontalHeaderItem(i)
            if header_item:
                header_item.setBackground(color_header)
                header_item.setForeground(text_color_header)
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                header_item.setFont(self._get_font(bold=True))
        
        # Set row heights
        self.grid_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        for i in range(len(hours)):
            self.grid_table.setRowHeight(i, 80)

    def _setup_classroom_colors(self, assignments: Dict[str, Tuple[str, int, int]]):
        """Setup a unique color for each classroom."""
        # Color palette for classrooms
        color_palette = [
            QColor(76, 175, 80),    # Green
            QColor(33, 150, 243),   # Blue
            QColor(255, 152, 0),    # Orange
            QColor(156, 39, 176),   # Purple
            QColor(244, 67, 54),    # Red
            QColor(0, 150, 136),    # Teal
            QColor(233, 30, 99),    # Pink
            QColor(63, 81, 181),    # Indigo
            QColor(255, 87, 34),    # Deep Orange
            QColor(103, 58, 183),   # Deep Purple
        ]
        
        self._classroom_colors = {}
        classrooms = sorted(set(classroom for classroom, _, _ in assignments.values()))
        
        for idx, classroom in enumerate(classrooms):
            self._classroom_colors[classroom] = color_palette[idx % len(color_palette)]

    def _get_font(self, bold: bool = False, size: int = 10):
        """Get a font with specified properties."""
        from PyQt6.QtGui import QFont
        font = QFont("Arial", size)
        font.setBold(bold)
        return font

    def _display_classroom_view(self, assignments: Dict[str, Tuple[str, int, int]], 
                                time_model: TimeModel):
        """Display assignments grouped by classroom."""
        # Group by classroom
        classroom_groups = {}
        for group_id, (classroom, day_i, block_i) in assignments.items():
            if classroom not in classroom_groups:
                classroom_groups[classroom] = []
            
            day_name, hour = time_model.to_external(day_i, block_i)
            classroom_groups[classroom].append((group_id, day_name, hour))
        
        # Calculate total rows
        total_rows = sum(len(groups) for groups in classroom_groups.values())
        
        self.classroom_table.clear()
        self.classroom_table.setRowCount(total_rows)
        self.classroom_table.setColumnCount(4)
        self.classroom_table.setHorizontalHeaderLabels([
            "Aula", "Grupo", "Día", "Hora"
        ])
        
        row = 0
        for classroom in sorted(classroom_groups.keys()):
            groups = sorted(classroom_groups[classroom], key=lambda x: (x[1], x[2]))
            
            for group_id, day_name, hour in groups:
                self.classroom_table.setItem(row, 0, QTableWidgetItem(classroom))
                self.classroom_table.setItem(row, 1, QTableWidgetItem(group_id))
                self.classroom_table.setItem(row, 2, QTableWidgetItem(day_name))
                self.classroom_table.setItem(row, 3, QTableWidgetItem(f"{hour}:00"))
                row += 1
        
        self.classroom_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _update_summary(self, assignments: Dict[str, Tuple[str, int, int]]):
        """Store summary data for the popup dialog."""
        self.summary_data = {
            'total_assignments': len(assignments),
            'classrooms_used': len(set(classroom for classroom, _, _ in assignments.values())),
            'courses_scheduled': len(set(group_id.rsplit('-G', 1)[0] for group_id in assignments.keys()))
        }

    def _show_summary_popup(self):
        """Show a popup dialog with the schedule summary."""
        if not self.summary_data:
            QMessageBox.information(self, "Información", "No hay horario generado aún.")
            return
        
        summary_text = (
            f"📊 Resumen del Horario\n\n"
            f"Total de asignaciones: {self.summary_data['total_assignments']}\n"
            f"Aulas utilizadas: {self.summary_data['classrooms_used']}\n"
            f"Cursos programados: {self.summary_data['courses_scheduled']}"
        )
        
        QMessageBox.information(self, "📊 Resumen", summary_text)
