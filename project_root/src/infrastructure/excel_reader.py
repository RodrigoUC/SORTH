# src/infrastructure/excel_reader.py

from typing import Dict, Tuple
import pandas as pd
import re

from ..scheduling.classroom import Classroom


DAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]


class ExcelReader:
    """
    Responsible for transforming the Excel input file into
    domain objects and structured availability data.
    """

    def __init__(self, file_path: str):
        self.file_path = file_path

    # ----------------------------
    # Public API
    # ----------------------------

    def load_classrooms(self) -> Dict[str, Classroom]:
        """
        Reads the sheet 'Capacidad aulas' and builds Classroom objects.
        If classroom name starts with 'L', it is treated as LAB.
        """
        df = pd.read_excel(self.file_path, sheet_name="Capacidad aulas")

        classrooms = {}

        for _, row in df.iterrows():
            name = str(row["# DE AULA"]).strip()

            if not name or name.lower() == "nan":
                continue

            capacity = int(row["CAPACIDAD"])
            room_type = "LAB" if name.startswith("L") else "REGULAR"

            classrooms[name] = Classroom(
                name=name,
                capacity=capacity,
                room_type=room_type
            )

        return classrooms

    def load_availability(self) -> Dict[Tuple[str, str, int], bool]:
        """
        Parses the sheet 'Aulas' and builds a map:
        (classroom_name, day, hour) -> available (bool)
        """
        df = pd.read_excel(self.file_path, sheet_name="Aulas", header=None)

        availability = {}
        blocks = self._detect_schedule_blocks(df)

        for block in blocks:
            classroom_name = block["classroom"]
            day_columns = block["day_columns"]
            hour_column = block["hour_column"]
            start_row = block["start_row"]
            end_row = block["end_row"]

            for row in range(start_row, end_row + 1):
                hour_value = df.iloc[row, hour_column]

                if pd.isna(hour_value):
                    continue

                hour = self._normalize_hour(hour_value)

                for col_index, day_name in day_columns.items():
                    cell_value = df.iloc[row, col_index]
                    available = pd.isna(cell_value)

                    availability[(classroom_name, day_name, hour)] = available

        return availability

    # ----------------------------
    # Internal helpers
    # ----------------------------

    def _detect_schedule_blocks(self, df: pd.DataFrame):
        """
        Detects schedule blocks dynamically by scanning for day headers.
        Returns list of dicts describing each block.
        """
        blocks = []

        for row_idx in range(len(df)):
            row = df.iloc[row_idx]

            if self._is_day_header_row(row):
                day_columns = self._extract_day_columns(row)
                classroom_name = self._find_classroom_name(df, row_idx)
                hour_column = self._detect_hour_column(df, row_idx)
                end_row = self._detect_block_end(df, row_idx, hour_column)

                blocks.append({
                    "classroom": classroom_name,
                    "day_columns": day_columns,
                    "hour_column": hour_column,
                    "start_row": row_idx + 1,
                    "end_row": end_row
                })

        return blocks

    def _is_day_header_row(self, row: pd.Series) -> bool:
        matches = sum(
            1 for value in row
            if isinstance(value, str) and value.strip() in DAY_NAMES
        )
        return matches >= 3

    def _extract_day_columns(self, row: pd.Series) -> Dict[int, str]:
        day_columns = {}

        for col_idx, value in enumerate(row):
            if isinstance(value, str) and value.strip() in DAY_NAMES:
                day_columns[col_idx] = value.strip()

        return day_columns

    def _find_classroom_name(self, df: pd.DataFrame, header_row_idx: int) -> str:
        for offset in range(1, 6):
            row_idx = header_row_idx - offset
            if row_idx < 0:
                break

            row = df.iloc[row_idx]
            for value in row:
                if isinstance(value, str):
                    value = value.strip()
                    if value and value not in DAY_NAMES:
                        return value

        raise ValueError(
            f"Could not determine classroom name near row {header_row_idx}"
        )

    def _detect_hour_column(self, df: pd.DataFrame, header_row_idx: int) -> int:
        for col_idx in range(df.shape[1]):
            consecutive_matches = 0

            for row_idx in range(header_row_idx + 1, min(header_row_idx + 10, len(df))):
                value = df.iloc[row_idx, col_idx]

                if self._looks_like_hour(value):
                    consecutive_matches += 1

            if consecutive_matches >= 3:
                return col_idx

        raise ValueError(f"Could not detect hour column below row {header_row_idx}")

    def _detect_block_end(self, df: pd.DataFrame, header_row_idx: int, hour_column: int) -> int:
        last_valid_row = header_row_idx

        for row_idx in range(header_row_idx + 1, len(df)):
            value = df.iloc[row_idx, hour_column]

            if pd.isna(value):
                break

            last_valid_row = row_idx

        return last_valid_row

    def _looks_like_hour(self, value) -> bool:
        if pd.isna(value):
            return False

        if hasattr(value, "hour"):
            return True

        if isinstance(value, str):
            return bool(re.match(r"^\d{1,2}:\d{2}", value.strip()))

        return False

    def _normalize_hour(self, value) -> int:
        if hasattr(value, "hour"):
            return int(value.hour)

        if isinstance(value, str):
            hour_part = value.strip().split(":")[0]
            return int(hour_part)

        raise ValueError(f"Unrecognized hour format: {value}")