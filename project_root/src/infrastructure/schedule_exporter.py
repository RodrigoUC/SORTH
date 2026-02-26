# src/infrastructure/schedule_exporter.py

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from ..scheduling.time_model import TimeModel


class ScheduleExporter:
    """
    Exports scheduling results to Excel or CSV formats.
    Provides both detailed and summary views of the schedule.
    """

    def __init__(self, time_model: TimeModel):
        self.time_model = time_model

    def to_excel(self, assignments: Dict[str, Tuple[str, int, int]], 
                 output_path: str,
                 include_grid: bool = True) -> None:
        """
        Export schedule to Excel file with multiple sheets.
        
        Args:
            assignments: Dictionary mapping group_id to (classroom, day_idx, block_idx)
            output_path: Path to save the Excel file
            include_grid: If True, creates a visual grid/timetable view
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Create detailed list
        detailed_df = self._create_detailed_dataframe(assignments)

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Grid view (visual timetable) - if requested
            if include_grid:
                self._write_grid_sheet(writer, assignments, 'Horario Visual')

            # Sheet 2: Detailed list
            detailed_df.to_excel(writer, sheet_name='Asignaciones', index=False)
            self._format_detailed_sheet(writer, 'Asignaciones', len(detailed_df))

            # Sheet 3: Summary by classroom
            classroom_summary = self._create_classroom_summary(assignments)
            classroom_summary.to_excel(writer, sheet_name='Por Aula', index=False)
            self._format_classroom_sheet(writer, 'Por Aula', len(classroom_summary))

        print(f"✅ Horario exportado a: {output_path}")

    def to_csv(self, assignments: Dict[str, Tuple[str, int, int]], 
               output_path: str) -> None:
        """
        Export schedule to CSV file (detailed list only).
        
        Args:
            assignments: Dictionary mapping group_id to (classroom, day_idx, block_idx)
            output_path: Path to save the CSV file
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        detailed_df = self._create_detailed_dataframe(assignments)
        detailed_df.to_csv(output_path, index=False, encoding='utf-8-sig')

        print(f"✅ Horario exportado a: {output_path}")

    def _write_grid_sheet(self, writer, assignments: Dict[str, Tuple[str, int, int]], 
                         sheet_name: str):
        """Write a visual grid/timetable sheet to Excel."""
        days = self.time_model.days
        hours = sorted(self.time_model.hours)

        # Create grid data
        grid_data = []
        for hour in hours:
            row = {'Hora': f"{hour}:00"}
            for day in days:
                row[day] = ""
            grid_data.append(row)

        # Fill grid with assignments
        for group_id, (classroom, day_i, block_i) in assignments.items():
            day_name, hour = self.time_model.to_external(day_i, block_i)
            course_code = group_id.rsplit('-G', 1)[0]
            group_num = group_id.rsplit('-G', 1)[1]
            cell_value = f"{course_code}-G{group_num}\n({classroom})"
            
            # Find the row for this hour
            for row in grid_data:
                if row['Hora'] == f"{hour}:00":
                    if row[day_name]:
                        row[day_name] += f"\n---\n{cell_value}"
                    else:
                        row[day_name] = cell_value
                    break

        # Create DataFrame and write
        grid_df = pd.DataFrame(grid_data)
        grid_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Create color mapping for classrooms
        classroom_colors = self._get_classroom_colors(assignments)

        # Format the sheet
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Styling
        header_fill = PatternFill(start_color="1967D2", end_color="1967D2", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        assignment_font = Font(color="000000", size=10, bold=True)
        assignment_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        hour_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
        hour_font = Font(bold=True, color="000000", size=11)
        hour_alignment = Alignment(horizontal="center", vertical="center")

        empty_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # Format cells
        for row_idx, row in enumerate(worksheet.iter_rows(min_row=1, max_row=len(grid_data) + 1, 
                                                           min_col=1, max_col=len(days) + 1), 1):
            for col_idx, cell in enumerate(row, 1):
                cell.border = thin_border

                if row_idx == 1:
                    # Header row
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = header_alignment
                elif col_idx == 1:
                    # Hour column
                    cell.fill = hour_fill
                    cell.font = hour_font
                    cell.alignment = hour_alignment
                else:
                    # Data cells
                    if cell.value:
                        # Extract classroom from cell value to get color
                        cell_text = str(cell.value)
                        classroom = None
                        for line in cell_text.split('\n'):
                            if '(' in line and ')' in line:
                                classroom = line.strip('()')
                                break
                        
                        if classroom in classroom_colors:
                            color_hex = classroom_colors[classroom]
                            cell.fill = PatternFill(start_color=color_hex, end_color=color_hex, fill_type="solid")
                        
                        cell.font = assignment_font
                        cell.alignment = assignment_alignment
                    else:
                        cell.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
                        cell.alignment = empty_alignment

        # Set column widths
        worksheet.column_dimensions['A'].width = 10
        for col_idx in range(2, len(days) + 2):
            col_letter = get_column_letter(col_idx)
            worksheet.column_dimensions[col_letter].width = 25

        # Set row heights
        worksheet.row_dimensions[1].height = 25
        for row_idx in range(2, len(grid_data) + 2):
            worksheet.row_dimensions[row_idx].height = 60

    def _get_classroom_colors(self, assignments: Dict[str, Tuple[str, int, int]]) -> Dict[str, str]:
        """Get a unique color for each classroom (as hex strings)."""
        # Color palette for classrooms (as hex codes)
        color_palette = [
            "4CAF50",    # Green
            "2196F3",    # Blue
            "FF9800",    # Orange
            "9C27B0",    # Purple
            "F44336",    # Red
            "009688",    # Teal
            "E91E63",    # Pink
            "3F51B5",    # Indigo
            "FF5722",    # Deep Orange
            "673AB7",    # Deep Purple
        ]
        
        classroom_colors = {}
        classrooms = sorted(set(classroom for classroom, _, _ in assignments.values()))
        
        for idx, classroom in enumerate(classrooms):
            classroom_colors[classroom] = color_palette[idx % len(color_palette)]
        
        return classroom_colors

    def _format_detailed_sheet(self, writer, sheet_name: str, num_rows: int):
        """Format the detailed assignments sheet."""
        worksheet = writer.sheets[sheet_name]
        
        header_fill = PatternFill(start_color="1967D2", end_color="1967D2", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Format header row
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Set column widths
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 15
        worksheet.column_dimensions['C'].width = 15
        worksheet.column_dimensions['D'].width = 12
        worksheet.column_dimensions['E'].width = 15
        worksheet.column_dimensions['F'].width = 10

    def _format_classroom_sheet(self, writer, sheet_name: str, num_rows: int):
        """Format the classroom summary sheet."""
        worksheet = writer.sheets[sheet_name]
        
        header_fill = PatternFill(start_color="1967D2", end_color="1967D2", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Format header row
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment

        # Set column widths
        worksheet.column_dimensions['A'].width = 15
        worksheet.column_dimensions['B'].width = 20
        worksheet.column_dimensions['C'].width = 12
        worksheet.column_dimensions['D'].width = 12

    def _create_detailed_dataframe(self, assignments: Dict[str, Tuple[str, int, int]]) -> pd.DataFrame:
        """Create a detailed list of all assignments."""
        rows = []

        for group_id, (classroom, day_i, block_i) in sorted(assignments.items()):
            day_name, hour = self.time_model.to_external(day_i, block_i)

            # Extract course code from group_id (format: "CODE-G1")
            course_code = group_id.rsplit('-G', 1)[0]

            rows.append({
                'Código Curso': course_code,
                'Grupo': group_id,
                'Aula': classroom,
                'Día': day_name,
                'Hora Inicio': f"{hour}:00",
                'Bloque': block_i + 1
            })

        return pd.DataFrame(rows)

    def _create_grid_dataframe(self, assignments: Dict[str, Tuple[str, int, int]]) -> pd.DataFrame:
        """Create a visual grid/timetable view (deprecated - use _write_grid_sheet instead)."""
        return pd.DataFrame()

    def _create_classroom_summary(self, assignments: Dict[str, Tuple[str, int, int]]) -> pd.DataFrame:
        """Create summary grouped by classroom."""
        classroom_groups = {}

        for group_id, (classroom, day_i, block_i) in assignments.items():
            if classroom not in classroom_groups:
                classroom_groups[classroom] = []

            day_name, hour = self.time_model.to_external(day_i, block_i)
            classroom_groups[classroom].append({
                'Grupo': group_id,
                'Día': day_name,
                'Hora': f"{hour}:00"
            })

        rows = []
        for classroom in sorted(classroom_groups.keys()):
            for assignment in sorted(classroom_groups[classroom], 
                                   key=lambda x: (x['Día'], x['Hora'])):
                rows.append({
                    'Aula': classroom,
                    'Grupo': assignment['Grupo'],
                    'Día': assignment['Día'],
                    'Hora': assignment['Hora']
                })

        return pd.DataFrame(rows)

    def print_summary(self, assignments: Dict[str, Tuple[str, int, int]]) -> None:
        """Print a formatted summary to console."""
        print("\n" + "="*60)
        print("RESUMEN DEL HORARIO GENERADO")
        print("="*60)
        print(f"Total de asignaciones: {len(assignments)}")
        
        # Group by classroom
        classrooms = set(classroom for classroom, _, _ in assignments.values())
        print(f"Aulas utilizadas: {len(classrooms)}")
        
        # Group by course
        courses = set(group_id.rsplit('-G', 1)[0] for group_id in assignments.keys())
        print(f"Cursos programados: {len(courses)}")
        
        print("="*60 + "\n")
