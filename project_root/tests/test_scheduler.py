from src.scheduling.scheduler import Scheduler
from src.scheduling.schedule_state import ScheduleState
from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.group import Group


def test_scheduler_assigns_all_groups():
    time_model = TimeModel(days=5, blocks_per_day=4)

    classrooms = [
        Classroom("Room1", 30, "Normal"),
        Classroom("Lab1", 25, "Laboratory")
    ]

    state = ScheduleState(time_model, classrooms)

    groups = [
        Group("C1-G1", "C1", 2, "Normal"),
        Group("C2-G1", "C2", 2, "Laboratory")
    ]

    scheduler = Scheduler()

    success = scheduler.schedule(state, groups)

    assert success is True

    for group in groups:
        assert group.is_assigned()