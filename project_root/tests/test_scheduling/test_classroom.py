from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom

def test_classroom_occupy_and_release():
    availability = {
        ("A1", "Lunes", 7): True,
        ("A1", "Lunes", 8): True,
    }

    tm = TimeModel.from_availability(availability)

    classroom = Classroom("A1", capacity=30, room_type="REGULAR", time_model=tm)

    day_i, block_i = tm.to_internal("Lunes", 7)

    assert classroom.is_available(day_i, block_i, 2)

    classroom.occupy(day_i, block_i, 2)

    assert not classroom.is_available(day_i, block_i, 2)

    classroom.release(day_i, block_i, 2)

    assert classroom.is_available(day_i, block_i, 2)