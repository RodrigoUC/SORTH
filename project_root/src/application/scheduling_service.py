# src/application/scheduling_service.py

from ..scheduling.time_model import TimeModel
from ..scheduling.schedule_state import ScheduleState
from ..scheduling.scheduler import Scheduler
from ..infrastructure.excel_reader import ExcelReader
from ..infrastructure.course_config_reader import CourseConfigReader


class SchedulingService:

    def __init__(self, excel_path: str, course_config_path: str):
        """
        Initialize the scheduling service.
        
        Args:
            excel_path: Path to Excel file containing classrooms and availability
            course_config_path: Path to JSON file containing course configuration
        """
        self.excel_path = excel_path
        self.course_config_path = course_config_path

    def run(self):
        # 1. Load infrastructure data
        excel_reader = ExcelReader(self.excel_path)
        course_reader = CourseConfigReader(self.course_config_path)

        classrooms = excel_reader.load_classrooms()
        availability = excel_reader.load_availability()
        courses = course_reader.load_courses()

        # 2. Build domain model
        time_model = TimeModel.from_availability(availability)

        schedule_state = ScheduleState(
            time_model=time_model,
            classrooms=list(classrooms.values())
        )

        for (classroom_name, day, hour), available in availability.items():
            if available:
                continue

            day_i, block_i = time_model.to_internal(day, hour)
            if classroom_name in schedule_state.classrooms:
                schedule_state.classrooms[classroom_name].occupy(day_i, block_i, 1)

        groups = []
        for course in courses:
            groups.extend(course.generate_groups())

        # 3. Run scheduler
        scheduler = Scheduler()
        success = scheduler.schedule(schedule_state, groups)

        # 4. Return result
        return schedule_state.assignments if success else None