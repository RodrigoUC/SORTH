# src/gui/main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QMessageBox,
                             QTabWidget, QStatusBar)
from PyQt6.QtCore import Qt
from pathlib import Path

from .course_manager_widget import CourseManagerWidget
from .schedule_viewer_widget import ScheduleViewerWidget
from ..application.scheduling_service import SchedulingService
from ..infrastructure.excel_reader import ExcelReader
from ..infrastructure.schedule_exporter import ScheduleExporter
from ..scheduling.time_model import TimeModel


class MainWindow(QMainWindow):
    """
    Main window of the SORTH scheduling application.
    """

    def __init__(self):
        super().__init__()
        self.excel_path = None
        self.courses = []
        self.current_schedule = None
        self.time_model = None
        
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("SORTH - Sistema de Organización de Horarios")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top section: File selection
        file_section = self._create_file_selection_section()
        main_layout.addLayout(file_section)

        # Tab widget for different views
        self.tabs = QTabWidget()
        
        # Tab 1: Course Manager
        self.course_manager = CourseManagerWidget()
        self.tabs.addTab(self.course_manager, "📚 Gestión de Cursos")
        
        # Tab 2: Schedule Viewer
        self.schedule_viewer = ScheduleViewerWidget()
        self.tabs.addTab(self.schedule_viewer, "📅 Horario Generado")
        
        main_layout.addWidget(self.tabs)

        # Bottom section: Actions
        actions_section = self._create_actions_section()
        main_layout.addLayout(actions_section)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo. Cargue un archivo Excel para comenzar.")

    def _create_file_selection_section(self) -> QVBoxLayout:
        """Create the file selection section."""
        layout = QVBoxLayout()

        # Instructions box
        instructions = QLabel(
            "📋 PASO 1: Cargar Archivo Excel\n\n"
            "El archivo Excel debe contener:\n"
            "  • Hoja 'Capacidad aulas': Código de aula y capacidad\n"
            "  • Hoja de disponibilidad: Horario de bloques ocupados por aula\n\n"
            "El sistema detectará automáticamente las aulas disponibles y sus horarios."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(
            "background-color: #E3F2FD; "
            "color: #1565C0; "
            "padding: 12px; "
            "border-left: 4px solid #1967D2; "
            "border-radius: 3px; "
            "font-size: 11px;"
        )
        layout.addWidget(instructions)

        # File selection row
        file_layout = QHBoxLayout()
        
        excel_label = QLabel("Archivo Excel:")
        excel_label.setStyleSheet("font-weight: bold;")
        self.excel_path_label = QLabel("No seleccionado")
        self.excel_path_label.setStyleSheet("color: #D32F2F; font-style: italic;")
        btn_load_excel = QPushButton("📂 Cargar Excel")
        btn_load_excel.clicked.connect(self.load_excel_file)
        btn_load_excel.setStyleSheet("""
            QPushButton {
                background-color: #1967D2;
                color: white;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)

        file_layout.addWidget(excel_label)
        file_layout.addWidget(self.excel_path_label, 1)
        file_layout.addWidget(btn_load_excel)
        
        layout.addLayout(file_layout)
        
        return layout

    def _create_actions_section(self) -> QHBoxLayout:
        """Create the actions button section."""
        layout = QHBoxLayout()

        # Generate schedule button
        self.btn_generate = QPushButton("🚀 Generar Horario")
        self.btn_generate.clicked.connect(self.generate_schedule)
        self.btn_generate.setEnabled(False)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        # Export button
        self.btn_export = QPushButton("💾 Exportar Resultados")
        self.btn_export.clicked.connect(self.export_schedule)
        self.btn_export.setEnabled(False)

        layout.addStretch()
        layout.addWidget(self.btn_generate)
        layout.addWidget(self.btn_export)

        return layout

    def load_excel_file(self):
        """Load Excel file with classroom and availability data."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )

        if file_path:
            try:
                self.excel_path = file_path
                self.excel_path_label.setText(Path(file_path).name)
                self.excel_path_label.setStyleSheet("color: green;")
                
                # Load availability to create time model
                reader = ExcelReader(self.excel_path)
                availability = reader.load_availability()
                self.time_model = TimeModel.from_availability(availability)
                
                self.status_bar.showMessage(f"✅ Excel cargado: {Path(file_path).name}")
                self.btn_generate.setEnabled(True)
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al cargar el archivo Excel:\n{str(e)}"
                )
                self.excel_path = None
                self.excel_path_label.setText("Error al cargar")
                self.excel_path_label.setStyleSheet("color: red;")

    def generate_schedule(self):
        """Generate the schedule based on courses and constraints."""
        if not self.excel_path:
            QMessageBox.warning(self, "Advertencia", "Por favor cargue un archivo Excel primero.")
            return

        courses = self.course_manager.get_courses()
        if not courses:
            QMessageBox.warning(self, "Advertencia", "Por favor agregue al menos un curso.")
            return

        try:
            self.status_bar.showMessage("⏳ Generando horario...")
            
            # Save courses to temporary config
            import json
            import tempfile
            
            temp_config = tempfile.NamedTemporaryFile(mode='w', suffix='.json', 
                                                     delete=False, encoding='utf-8')
            json.dump({"courses": courses}, temp_config)
            temp_config.close()

            # Run scheduling service
            service = SchedulingService(self.excel_path, temp_config.name)
            assignments = service.run()

            # Clean up temp file
            Path(temp_config.name).unlink()

            if assignments:
                self.current_schedule = assignments
                self.schedule_viewer.display_schedule(assignments, self.time_model)
                self.tabs.setCurrentIndex(1)  # Switch to schedule viewer tab
                self.btn_export.setEnabled(True)
                self.status_bar.showMessage(f"✅ Horario generado exitosamente ({len(assignments)} asignaciones)")
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Horario generado exitosamente!\n\n"
                    f"Total de asignaciones: {len(assignments)}\n"
                    f"Aulas utilizadas: {len(set(a[0] for a in assignments.values()))}\n"
                    f"Cursos programados: {len(set(g.rsplit('-G', 1)[0] for g in assignments.keys()))}"
                )
            else:
                self.status_bar.showMessage("❌ No se pudo generar el horario")
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudo generar un horario válido.\n\n"
                    "Posibles causas:\n"
                    "- No hay suficientes aulas disponibles\n"
                    "- Conflictos de horario\n"
                    "- Restricciones muy estrictas"
                )

        except Exception as e:
            self.status_bar.showMessage("❌ Error al generar horario")
            QMessageBox.critical(
                self,
                "Error",
                f"Error al generar el horario:\n{str(e)}"
            )

    def export_schedule(self):
        """Export the generated schedule to Excel/CSV."""
        if not self.current_schedule or not self.time_model:
            QMessageBox.warning(self, "Advertencia", "No hay horario para exportar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar horario",
            "horario.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )

        if file_path:
            try:
                exporter = ScheduleExporter(self.time_model)
                
                if file_path.endswith('.csv'):
                    exporter.to_csv(self.current_schedule, file_path)
                else:
                    exporter.to_excel(self.current_schedule, file_path, include_grid=True)
                
                self.status_bar.showMessage(f"✅ Horario exportado a {Path(file_path).name}")
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Horario exportado exitosamente a:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error al exportar el horario:\n{str(e)}"
                )
