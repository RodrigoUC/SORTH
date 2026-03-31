from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.schedule_state import ScheduleState
from src.scheduling.group import Group


def _make_state():
    tm = TimeModel(["Lunes", "Martes"])
    classroom = Classroom("A1", capacity=30, room_type="REGULAR")
    return ScheduleState(tm, [classroom]), tm


def test_assign_and_unassign():
    state, tm = _make_state()
    group = Group("G1", duration_min=120, required_room_type="REGULAR", size=20)

    day = tm.to_day_index("Lunes")
    assert state.assign(group, "A1", day, 480)   # 08:00-10:00
    assert group.is_assigned()
    assert group.assignment == ("A1", day, 480, 600)

    state.unassign(group)
    assert not group.is_assigned()
    assert "G1" not in state.assignments


def test_assign_fails_on_overlap():
    state, tm = _make_state()
    g1 = Group("G1", duration_min=120, required_room_type="REGULAR", size=20)
    g2 = Group("G2", duration_min=120, required_room_type="REGULAR", size=20)

    day = tm.to_day_index("Lunes")
    assert state.assign(g1, "A1", day, 480)
    assert not state.assign(g2, "A1", day, 480)   # same slot → conflict


def test_assign_fails_wrong_room_type():
    state, tm = _make_state()
    group = Group("G1", duration_min=60, required_room_type="LAB", size=10)
    day = tm.to_day_index("Lunes")
    assert not state.assign(group, "A1", day, 480)


def test_assign_fails_capacity():
    state, tm = _make_state()
    group = Group("G1", duration_min=60, required_room_type="REGULAR", size=50)
    day = tm.to_day_index("Lunes")
    assert not state.assign(group, "A1", day, 480)


def test_assign_fails_overlaps_lunch():
    state, tm = _make_state()
    group = Group("G1", duration_min=120, required_room_type="REGULAR", size=10)
    day = tm.to_day_index("Lunes")
    # 11:30-13:30 overlaps lunch (12:00-13:00)
    assert not state.assign(group, "A1", day, 690)
