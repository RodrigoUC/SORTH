from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.schedule_state import ScheduleState
from src.scheduling.group import Group

def test_schedule_state_assign_and_unassign():
    availability = {
        ("A1", "Lunes", 7): True,
        ("A1", "Lunes", 8): True,
    }

    tm = TimeModel.from_availability(availability)

    classroom = Classroom("A1", 30, "REGULAR", tm)
    state = ScheduleState(tm, [classroom])

    group = Group("G1", duration=2, required_room_type="REGULAR", size=20)

    day_i, block_i = tm.to_internal("Lunes", 7)

    assert state.assign(group, "A1", day_i, block_i)

    assert group.is_assigned()

    state.unassign(group)

    assert not group.is_assigned()