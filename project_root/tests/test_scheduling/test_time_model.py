from src.scheduling.time_model import TimeModel

def test_time_model_translation():
    availability = {
        ("A1", "Lunes", 7): True,
        ("A1", "Martes", 8): True,
    }

    tm = TimeModel.from_availability(availability)

    day_i, block_i = tm.to_internal("Lunes", 7)

    assert tm.to_external(day_i, block_i) == ("Lunes", 7)


def test_time_model_valid_slot():
    availability = {
        ("A1", "Lunes", 7): True,
        ("A1", "Lunes", 8): True,
    }

    tm = TimeModel.from_availability(availability)

    day_i, block_i = tm.to_internal("Lunes", 7)

    assert tm.is_valid_slot(day_i, block_i, duration=2)
    assert not tm.is_valid_slot(day_i, block_i, duration=3)