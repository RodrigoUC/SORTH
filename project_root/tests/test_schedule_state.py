from src.scheduling.schedule_state import ScheduleState
from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.group import Group


def test_successful_assignment():
    time_model = TimeModel(days=5, blocks_per_day=8)
    classroom = Classroom("RoomA", 30, "Normal")

    state = ScheduleState(
        time_model=time_model,
        classrooms=[classroom]
    )

    group = Group(
        group_id="MAT101-G1",
        course_code="MAT101",
        duration=2,
        required_room_type="Normal"
    )

    success = state.assign(group, classroom_name="RoomA", day=1, start_block=3)

    assert success is True
    assert group.is_assigned() is True


def test_assignment_fails_if_room_occupied():
    time_model = TimeModel(days=5, blocks_per_day=8)
    classroom = Classroom("RoomA", 30, "Normal")

    state = ScheduleState(
        time_model=time_model,
        classrooms=[classroom]
    )

    group1 = Group("C1-G1", "C1", 2, "Normal")
    group2 = Group("C2-G1", "C2", 2, "Normal")

    state.assign(group1, "RoomA", day=1, start_block=3)

    success = state.assign(group2, "RoomA", day=1, start_block=3)

    assert success is False