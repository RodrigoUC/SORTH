from datetime import datetime
from src.application.scheduling_service import SchedulingService
from src.infrastructure.excel_reader import ExcelReader
from src.infrastructure.schedule_exporter import ScheduleExporter
from src.scheduling.time_model import TimeModel


def main():
    excel_path = "data/input/test_small.xlsx"
    course_config_path = "data/input/courses_config.json"
    
    print("🔄 Generando horario...")
    service = SchedulingService(excel_path, course_config_path)
    assignments = service.run()

    if not assignments:
        print("❌ No se pudo generar un horario válido.")
        return

    # Load time model for export
    reader = ExcelReader(excel_path)
    availability = reader.load_availability()
    time_model = TimeModel.from_availability(availability)

    # Print to console
    print("\n📋 ASIGNACIONES GENERADAS:\n")
    for group_id, assignment in sorted(assignments.items()):
        classroom, day_i, block_i = assignment
        day_name, hour = time_model.to_external(day_i, block_i)
        print(f"  {group_id} -> {classroom} {day_name} {hour}:00")

    # Export results
    exporter = ScheduleExporter(time_model)
    exporter.print_summary(assignments)
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel = f"data/output/horario_{timestamp}.xlsx"
    output_csv = f"data/output/horario_{timestamp}.csv"
    
    exporter.to_excel(assignments, output_excel, include_grid=True)
    exporter.to_csv(assignments, output_csv)
    
    print(f"\n✅ Proceso completado exitosamente!")

if __name__ == "__main__":
    main()