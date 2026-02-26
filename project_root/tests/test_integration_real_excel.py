from pathlib import Path

from src.application.scheduling_service import SchedulingService


def test_real_excel_integration():
    base_dir = Path(__file__).resolve().parents[1]
    excel_path = base_dir / "data" / "input" / "test_small.xlsx"
    course_config_path = base_dir / "data" / "input" / "courses_config.json"

    service = SchedulingService(str(excel_path), str(course_config_path))

    assignments = service.run()

    assert assignments is not None
    assert len(assignments) > 0