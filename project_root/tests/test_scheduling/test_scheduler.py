from src.scheduling.scheduler import Scheduler
from src.scheduling.schedule_state import ScheduleState
from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.group import Group


def _make_state(days=None, capacity=30):
    tm = TimeModel(days or ["Lunes", "Martes"])
    classroom = Classroom("A1", capacity=capacity, room_type="REGULAR")
    return ScheduleState(tm, [classroom]), tm


def test_scheduler_assigns_single_group():
    state, _ = _make_state()
    group = Group("G1", duration_min=120, required_room_type="REGULAR", size=10)
    assert Scheduler().schedule(state, [group])
    assert group.is_assigned()


def test_scheduler_two_groups_same_classroom():
    state, _ = _make_state()
    g1 = Group("G1", duration_min=120, required_room_type="REGULAR", size=10)
    g2 = Group("G2", duration_min=120, required_room_type="REGULAR", size=10)
    # Two groups can fit in the same classroom on different slots/days
    assert Scheduler().schedule(state, [g1, g2])
    assert g1.is_assigned()
    assert g2.is_assigned()
    # They must not overlap
    assert not (g1.assignment[1] == g2.assignment[1] and
                g1.assignment[2] < g2.assignment[3] and
                g2.assignment[2] < g1.assignment[3])


def test_scheduler_no_solution_capacity():
    state, tm = _make_state(capacity=5)
    group = Group("G1", duration_min=60, required_room_type="REGULAR", size=30)
    assert not Scheduler().schedule(state, [group])


def test_scheduler_respects_preferred_day():
    state, tm = _make_state(["Lunes", "Martes"])
    group = Group("G1", duration_min=60, required_room_type="REGULAR",
                  size=10, preferred_day="Martes")
    assert Scheduler().schedule(state, [group])
    _, assigned_day, _, _ = group.assignment
    assert tm.to_day_name(assigned_day) == "Martes"


def test_scheduler_respects_preferred_start():
    state, _ = _make_state()
    group = Group("G1", duration_min=60, required_room_type="REGULAR",
                  size=10, preferred_start_min=480)
    assert Scheduler().schedule(state, [group])
    _, _, start, _ = group.assignment
    assert start == 480
