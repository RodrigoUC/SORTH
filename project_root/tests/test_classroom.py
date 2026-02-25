from src.scheduling.classroom import Classroom


def test_classroom_initialization():
    classroom = Classroom(
        name="Lab1",
        capacity=30,
        room_type="Laboratory"
    )

    assert classroom.name == "Lab1"
    assert classroom.capacity == 30
    assert classroom.room_type == "Laboratory"


def test_classroom_availability_and_occupation():
    classroom = Classroom(
        name="RoomA",
        capacity=40,
        room_type="Normal"
    )

    day = 1
    start_block = 3
    duration = 2

    assert classroom.is_available(day, start_block, duration) is True

    classroom.occupy(day, start_block, duration)

    assert classroom.is_available(day, start_block, duration) is False