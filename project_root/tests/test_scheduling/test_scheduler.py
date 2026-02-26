from src.scheduling.scheduler import Scheduler
from src.scheduling.schedule_state import ScheduleState
from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.group import Group

def test_scheduler_simple_case():
    availability = {
        ("A1", "Lunes", 7): True,
        ("A1", "Lunes", 8): True,
    }

    tm = TimeModel.from_availability(availability)

    classroom = Classroom("A1", 30, "REGULAR", tm)
    state = ScheduleState(tm, [classroom])

    group = Group("G1", duration=1, required_room_type="REGULAR", size=10)

    scheduler = Scheduler()

    result = scheduler.schedule(state, [group])

    assert result
    assert group.is_assigned()

def test_scheduler_no_solution():
    availability = {
        ("A1", "Lunes", 7): True,
    }

    tm = TimeModel.from_availability(availability)

    classroom = Classroom("A1", 30, "REGULAR", tm)
    state = ScheduleState(tm, [classroom])

    group1 = Group("G1", duration=1, required_room_type="REGULAR", size=10)
    group2 = Group("G2", duration=1, required_room_type="REGULAR", size=10)

    scheduler = Scheduler()

    result = scheduler.schedule(state, [group1, group2])

    assert not result