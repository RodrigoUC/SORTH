import pytest
from src.scheduling.course import Course


def test_generate_groups_creates_correct_number_of_groups():
    course = Course(
        code="BIO101",
        number_of_groups=3,
        duration=2,
        required_room_type="Laboratory",
        suggested_classroom="Lab1"
    )

    groups = course.generate_groups()

    assert len(groups) == 3
    assert groups[0].group_id == "BIO101-G1"
    assert groups[1].group_id == "BIO101-G2"
    assert groups[2].group_id == "BIO101-G3"


def test_generated_groups_inherit_course_properties():
    course = Course(
        code="MAT200",
        number_of_groups=2,
        duration=4,
        required_room_type="Normal",
        suggested_classroom=None
    )

    groups = course.generate_groups()

    for group in groups:
        assert group.duration == 4
        assert group.required_room_type == "Normal"
        assert group.suggested_classroom is None