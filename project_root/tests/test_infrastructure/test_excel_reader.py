import pandas as pd

from src.infrastructure.excel_reader import ExcelReader


def test_is_day_header_row_detects_valid_header():
    reader = ExcelReader("dummy.xlsx")

    row = pd.Series([
        None,
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        None
    ])

    assert reader._is_day_header_row(row) is True


def test_is_day_header_row_rejects_invalid_header():
    reader = ExcelReader("dummy.xlsx")

    row = pd.Series([
        "Algo",
        "Texto",
        "No",
        "Relacionado"
    ])

    assert reader._is_day_header_row(row) is False

def test_detect_hour_column():
    reader = ExcelReader("dummy.xlsx")

    data = [
        ["Aula 101", None, None],
        [None, "Lunes", "Martes"],
        ["7:00", None, None],
        ["8:00", None, None],
        ["9:00", None, None],
    ]

    df = pd.DataFrame(data)

    hour_column = reader._detect_hour_column(df, header_row_idx=1)

    assert hour_column == 0

def test_detect_schedule_blocks_single_block():
    reader = ExcelReader("dummy.xlsx")

    data = [
        ["Aula 101", None, None, None],
        [None, "Lunes", "Martes", "Miércoles"],
        ["7:00", None, "OCUPADO", None],
        ["8:00", None, None, None],
        ["9:00", "X", None, None],
        [None, None, None, None],
    ]

    df = pd.DataFrame(data)

    blocks = reader._detect_schedule_blocks(df)

    assert len(blocks) == 1

    block = blocks[0]

    assert block["classroom"] == "Aula 101"
    assert block["hour_column"] == 0
    assert block["start_row"] == 2
    assert block["end_row"] == 4

def test_load_availability_builds_correct_map(monkeypatch):
    reader = ExcelReader("dummy.xlsx")

    data = [
        ["Aula 101", None, None, None],
        [None, "Lunes", "Martes", "Miércoles"],
        ["7:00", None, "OCUPADO", None],
        ["8:00", None, None, None],
        ["9:00", None, None, None],
        ["10:00", None, None, None],
    ]

    df_mock = pd.DataFrame(data)

    # Mock read_excel to return our DataFrame
    def mock_read_excel(*args, **kwargs):
        return df_mock

    monkeypatch.setattr("src.infrastructure.excel_reader.pd.read_excel", mock_read_excel)

    availability = reader.load_availability()

    assert availability[("Aula 101", "Lunes", 7)] is True
    assert availability[("Aula 101", "Martes", 7)] is False
    assert availability[("Aula 101", "Miércoles", 7)] is True
    assert availability[("Aula 101", "Lunes", 8)] is True

def test_load_classrooms_builds_objects(monkeypatch):
    reader = ExcelReader("dummy.xlsx")

    data = {
        "# DE AULA": ["101", "L201"],
        "CAPACIDAD": [30, 25]
    }

    df_mock = pd.DataFrame(data)

    def mock_read_excel(*args, **kwargs):
        return df_mock

    monkeypatch.setattr("src.infrastructure.excel_reader.pd.read_excel", mock_read_excel)

    classrooms = reader.load_classrooms()

    assert classrooms["101"].room_type == "REGULAR"
    assert classrooms["L201"].room_type == "LAB"
    assert classrooms["L201"].capacity == 25