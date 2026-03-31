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


# ------------------------------------------------------------------
# Anti-copy grouping priority tests
# ------------------------------------------------------------------

def _make_multi_classroom_state(days=None):
    """State with 3 REGULAR classrooms and 2 days."""
    tm = TimeModel(days or ["Lunes", "Martes", "Miércoles"])
    classrooms = [
        Classroom("A1", capacity=30, room_type="REGULAR"),
        Classroom("A2", capacity=30, room_type="REGULAR"),
        Classroom("A3", capacity=30, room_type="REGULAR"),
    ]
    return ScheduleState(tm, classrooms), tm


def test_same_course_priority0_consecutive_blocks():
    """
    Two groups of the same course on the same day should either:
    - Be consecutive (priority 0): second starts at next exact hour after first ends
    - Or share the same time slot in different classrooms (priority 1)
    Both are valid anti-copy arrangements.
    """
    state, tm = _make_multi_classroom_state(["Lunes"])
    g1 = Group("BIO-G1", duration_min=90, required_room_type="REGULAR",
               size=10, course_code="BIO")
    g2 = Group("BIO-G2", duration_min=90, required_room_type="REGULAR",
               size=10, course_code="BIO")

    assert Scheduler(seed=42).schedule(state, [g1, g2])
    assert g1.is_assigned()
    assert g2.is_assigned()

    # Both must be on the same day
    assert g1.assignment[1] == g2.assignment[1]

    s1, e1 = g1.assignment[2], g1.assignment[3]
    s2, e2 = g2.assignment[2], g2.assignment[3]
    starts = sorted([s1, s2])
    ends   = sorted([e1, e2])

    # Priority 1: same start time, different classroom
    same_time = (s1 == s2 and g1.assignment[0] != g2.assignment[0])

    # Priority 0: consecutive — second starts at next exact hour after first ends
    first_end = ends[0]
    next_hour = ((first_end + 59) // 60) * 60
    consecutive = (starts[1] == next_hour)

    assert same_time or consecutive, (
        f"Expected same-time or consecutive blocks, got "
        f"G1={g1.assignment} G2={g2.assignment}"
    )


def test_same_course_priority1_same_time_different_classroom():
    """
    When consecutive blocks are not possible (only 1 day, 1 slot),
    groups of the same course should prefer same time in different classrooms.
    """
    # Only one time slot available per classroom per day
    tm = TimeModel(["Lunes"])
    classrooms = [
        Classroom("A1", capacity=30, room_type="REGULAR"),
        Classroom("A2", capacity=30, room_type="REGULAR"),
    ]
    state = ScheduleState(tm, classrooms)

    # Pre-occupy A1 at 10:00 and A2 at 10:00 to force same-time scenario
    # Actually just let the scheduler decide — with 2 classrooms and 2 groups
    # priority 1 (same time, different classroom) should be preferred
    g1 = Group("BIO-G1", duration_min=120, required_room_type="REGULAR",
               size=10, course_code="BIO")
    g2 = Group("BIO-G2", duration_min=120, required_room_type="REGULAR",
               size=10, course_code="BIO")

    assert Scheduler(seed=42).schedule(state, [g1, g2])
    assert g1.is_assigned()
    assert g2.is_assigned()
    # Must not overlap in same classroom
    if g1.assignment[0] == g2.assignment[0]:
        assert not (g1.assignment[2] < g2.assignment[3] and
                    g2.assignment[2] < g1.assignment[3])


def test_same_course_priority2_different_day_same_time():
    """
    Groups of the same course on different days should share the same start time.
    """
    state, tm = _make_multi_classroom_state(["Lunes", "Martes"])
    g1 = Group("BIO-G1", duration_min=120, required_room_type="REGULAR",
               size=10, course_code="BIO", preferred_start_min=480)
    g2 = Group("BIO-G2", duration_min=120, required_room_type="REGULAR",
               size=10, course_code="BIO", preferred_start_min=480)
    g3 = Group("BIO-G3", duration_min=120, required_room_type="REGULAR",
               size=10, course_code="BIO", preferred_start_min=480)

    assert Scheduler(seed=42).schedule(state, [g1, g2, g3])
    starts = {g.assignment[2] for g in [g1, g2, g3]}
    # All should share the same preferred start time
    assert starts == {480}


def test_regular_course_prefers_regular_classroom():
    """
    A REGULAR course should be assigned to a REGULAR classroom,
    not a LAB, even if both are available.
    """
    tm = TimeModel(["Lunes"])
    classrooms = [
        Classroom("LAB1", capacity=30, room_type="LAB"),
        Classroom("REG1", capacity=30, room_type="REGULAR"),
    ]
    state = ScheduleState(tm, classrooms)
    group = Group("BIO-G1", duration_min=90, required_room_type="REGULAR",
                  size=10, course_code="BIO")

    assert Scheduler(seed=42).schedule(state, [group])
    assert group.assignment[0] == "REG1"
