from src.scheduling.time_model import TimeModel


def test_time_model_initialization():
    model = TimeModel(days=5, blocks_per_day=8)

    assert model.days == 5
    assert model.blocks_per_day == 8


def test_valid_time_slot():
    model = TimeModel(days=5, blocks_per_day=8)

    assert model.is_valid_slot(day=1, start_block=3, duration=2) is True
    assert model.is_valid_slot(day=5, start_block=7, duration=2) is False
    assert model.is_valid_slot(day=6, start_block=1, duration=1) is False
    assert model.is_valid_slot(day=1, start_block=9, duration=1) is False