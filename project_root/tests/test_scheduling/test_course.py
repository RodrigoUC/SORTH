from src.scheduling.course import Course, SPLIT_THRESHOLD_MIN


def test_generate_groups_correct_count():
    course = Course(
        code="BIO101",
        number_of_groups=3,
        duration_min=120,
        required_room_type="LAB",
    )
    groups = course.generate_groups()
    assert len(groups) == 3
    assert groups[0].group_id == "BIO101-G1"
    assert groups[2].group_id == "BIO101-G3"


def test_groups_inherit_course_properties():
    course = Course(
        code="MAT200",
        number_of_groups=2,
        duration_min=90,
        required_room_type="REGULAR",
        preferred_start_min=480,
        preferred_day="Lunes",
    )
    groups = course.generate_groups()
    for g in groups:
        assert g.duration_min == 90
        assert g.required_room_type == "REGULAR"
        assert g.preferred_start_min == 480
        assert g.preferred_day == "Lunes"


def test_long_course_splits_into_subgroups():
    # 240 min > SPLIT_THRESHOLD_MIN (180) → should split into 2 parts of 120
    course = Course(
        code="BIO300",
        number_of_groups=1,
        duration_min=240,
        required_room_type="REGULAR",
    )
    groups = course.generate_groups()
    assert len(groups) == 2
    assert groups[0].group_id == "BIO300-G1-P1"
    assert groups[1].group_id == "BIO300-G1-P2"
    assert groups[0].parent_group_id == "BIO300-G1"
    assert groups[0].duration_min == 120
    assert groups[1].duration_min == 120


def test_short_course_no_split():
    course = Course(
        code="BIO100",
        number_of_groups=1,
        duration_min=SPLIT_THRESHOLD_MIN,
        required_room_type="REGULAR",
    )
    groups = course.generate_groups()
    assert len(groups) == 1
    assert groups[0].parent_group_id is None
