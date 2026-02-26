# src/application/scheduling_service.py

from ..scheduling.time_model import TimeModel
from ..scheduling.schedule_state import ScheduleState
from ..scheduling.scheduler import Scheduler
from ..infrastructure.excel_reader import ExcelReader


class SchedulingService:

    def __init__(self, excel_path: str):
        self.excel_path = excel_path

    def run(self):
        # 1. Load infrastructure data
        reader = ExcelReader(self.excel_path)

        classrooms = reader.load_classrooms()
        availability = reader.load_availability()
        courses = reader.load_courses()  # si ya lo implementaste

        # 2. Build domain model
        time_model = TimeModel.from_availability(availability)

        schedule_state = ScheduleState(
            classrooms=classrooms,
            time_model=time_model,
            availability=availability
        )

        # 3. Run scheduler
        scheduler = Scheduler(schedule_state)
        assignments = scheduler.solve(courses)

        # 4. Return result
        return assignments