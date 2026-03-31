# src/infrastructure/excel_reader.py

import pandas as pd
import unicodedata
from typing import Dict

from ..scheduling.classroom import Classroom
from ..scheduling.course import Course
from ..scheduling.time_model import TimeModel

# Mapping from Excel day abbreviation to full Spanish name
DAY_ABBR = {
    "L": "Lunes",
    "I": "Martes",
    "M": "Miércoles",
    "J": "Jueves",
    "V": "Viernes",
    "S": "Sábado",
}


class ExcelReader:

    def __init__(self, file_path: str):
        self.file_path = file_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_classrooms(self) -> Dict[str, Classroom]:
        """
        Read sheet 'Aulas' and build Classroom objects.
        Columns: # DE AULA, DESCRIPCIÓN, CAMPUS, CAPACIDAD, CAPACIDAD 80%
        Room type: starts with 'L' → LAB, otherwise → REGULAR.
        """
        df = pd.read_excel(self.file_path, sheet_name="Aulas")

        classrooms = {}
        for _, row in df.iterrows():
            raw_name = row.get("# DE AULA")
            if pd.isna(raw_name):
                continue

            name = str(raw_name).strip()
            if not name:
                continue

            capacity_raw = row.get("CAPACIDAD")
            capacity = int(capacity_raw) if pd.notna(capacity_raw) else 0

            description_raw = row.get("DESCRIPCIÓN")
            description = str(description_raw).strip() if pd.notna(description_raw) else ""

            campus_raw = row.get("CAMPUS")
            campus = str(campus_raw).strip() if pd.notna(campus_raw) else ""

            room_type = "LAB" if name.startswith("L") else "REGULAR"

            classrooms[name] = Classroom(
                name=name,
                capacity=capacity,
                room_type=room_type,
                description=description,
                campus=campus,
            )

        return classrooms

    def load_courses(self, known_classrooms: set[str] | None = None) -> list[Course]:
        """
        Read sheet 'Cursos' and build Course objects.

        Columns: Curso, Nombre de Curso, Cantidad de Grupos, Horas, Aula, Días

        Each row represents one suggested group of a course.
        Multiple rows with the same course code → multiple groups.

        Horas format: 'HHMM-HHMM' (e.g. '0800-1055') or '-' / blank → None
        Días format:  single abbreviation or comma-separated (e.g. 'L', 'L,M')

        If known_classrooms is provided, any Aula reference not in that set
        is silently ignored (treated as no classroom preference).
        """
        if known_classrooms is None:
            known_classrooms = set(self.load_classrooms().keys())

        df = pd.read_excel(self.file_path, sheet_name="Cursos")

        # Normalize column names for robust matching
        col_map = self._build_col_map(df.columns)

        course_rows: dict[str, list[dict]] = {}

        for _, row in df.iterrows():
            code_raw = self._get(row, col_map, "curso")
            if code_raw is None:
                continue
            code = str(code_raw).strip()
            if not code:
                continue

            name_raw = self._get(row, col_map, "nombre")
            name = str(name_raw).strip() if name_raw is not None else None

            horas_raw = self._get(row, col_map, "horas")
            start_min, end_min = self._parse_horas(horas_raw)

            aula_raw = self._get(row, col_map, "aula")
            aula = str(aula_raw).strip() if aula_raw is not None else None
            if aula and aula.lower() in ("nan", "-", ""):
                aula = None
            # Ignore aula references that don't exist in the classrooms sheet
            if aula and aula not in known_classrooms:
                aula = None

            dias_raw = self._get(row, col_map, "dias")
            days = self._parse_dias(dias_raw)

            course_rows.setdefault(code, []).append({
                "name": name,
                "start_min": start_min,
                "end_min": end_min,
                "aula": aula,
                "days": days,
            })

        classrooms_info = self.load_classrooms()

        courses = []
        for code, rows in course_rows.items():
            name = next((r["name"] for r in rows if r["name"]), None)
            number_of_groups = len(rows)
            duration_min = self._most_common_duration(rows)
            suggested_classroom = self._most_common_aula(rows)
            preferred_day = self._most_common_day(rows)
            preferred_start_min = self._most_common_start(rows)

            # Infer room type from the suggested classroom's actual type.
            # Fall back to code-suffix heuristic only when no known classroom.
            if suggested_classroom and suggested_classroom in classrooms_info:
                room_type = classrooms_info[suggested_classroom].room_type
            else:
                room_type = self._infer_room_type(code)

            # Per-group suggestions: preserve each row's individual aula/day/hour
            group_suggestions = [
                {
                    "aula": r["aula"],
                    "preferred_day": r["days"][0] if r["days"] else None,
                    "preferred_start_min": r["start_min"],
                }
                for r in rows
            ]

            courses.append(Course(
                code=code,
                name=name,
                number_of_groups=number_of_groups,
                duration_min=duration_min,
                required_room_type=room_type,
                suggested_classroom=suggested_classroom,
                preferred_day=preferred_day,
                preferred_start_min=preferred_start_min,
                group_suggestions=group_suggestions,
            ))

        return courses

    def load_course_classroom_map(self, known_classrooms: set[str] | None = None) -> dict[str, list[str]]:
        """
        Return a mapping: classroom_name -> [course_codes] based on the Aula
        column in the Cursos sheet. Used to set classroom restrictions.
        Only includes classrooms present in known_classrooms (if provided).
        """
        if known_classrooms is None:
            known_classrooms = set(self.load_classrooms().keys())

        df = pd.read_excel(self.file_path, sheet_name="Cursos")
        col_map = self._build_col_map(df.columns)

        classroom_courses: dict[str, list[str]] = {}
        for _, row in df.iterrows():
            code_raw = self._get(row, col_map, "curso")
            aula_raw = self._get(row, col_map, "aula")

            if code_raw is None or aula_raw is None:
                continue

            code = str(code_raw).strip()
            aula = str(aula_raw).strip()

            if not code or not aula or aula.lower() in ("nan", "-", ""):
                continue
            if aula not in known_classrooms:
                continue

            classroom_courses.setdefault(aula, [])
            if code not in classroom_courses[aula]:
                classroom_courses[aula].append(code)

        return classroom_courses

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_horas(self, value) -> tuple[int | None, int | None]:
        """
        Parse 'HHMM-HHMM' into (start_min, end_min).
        Returns (None, None) for blank or '-' values.
        """
        if value is None or pd.isna(value):
            return None, None
        s = str(value).strip()
        if s in ("", "-"):
            return None, None
        if "-" in s:
            parts = s.split("-")
            if len(parts) == 2:
                try:
                    start = TimeModel.hhmm_to_minutes(parts[0].strip())
                    end   = TimeModel.hhmm_to_minutes(parts[1].strip())
                    return start, end
                except (ValueError, IndexError):
                    pass
        return None, None

    def _parse_dias(self, value) -> list[str]:
        """
        Parse day abbreviation(s) into full Spanish day names.
        Accepts single value ('L') or comma-separated ('L,M').
        Returns empty list if blank/null.
        """
        if value is None or pd.isna(value):
            return []
        s = str(value).strip()
        if not s or s == "-":
            return []
        result = []
        for abbr in s.split(","):
            abbr = abbr.strip().upper()
            if abbr in DAY_ABBR:
                result.append(DAY_ABBR[abbr])
        return result

    def _infer_room_type(self, code: str) -> str:
        upper = code.strip().upper()
        if upper.endswith("L") or upper.endswith("P"):
            return "LAB"
        return "REGULAR"

    # ------------------------------------------------------------------
    # Column mapping
    # ------------------------------------------------------------------

    def _build_col_map(self, columns) -> dict[str, str]:
        """
        Build a normalized name → original name mapping for DataFrame columns.
        """
        mapping = {}
        for col in columns:
            normalized = self._normalize(str(col))
            mapping[normalized] = col
        return mapping

    def _normalize(self, text: str) -> str:
        text = text.strip().lower()
        text = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in text if not unicodedata.combining(ch))

    def _get(self, row, col_map: dict, key: str):
        """
        Get a value from a row using a partial normalized key match.
        Returns None if column not found or value is NaN.
        """
        for norm_col, orig_col in col_map.items():
            if key in norm_col:
                val = row[orig_col]
                return None if pd.isna(val) else val
        return None

    # ------------------------------------------------------------------
    # Aggregation helpers (most common value across group rows)
    # ------------------------------------------------------------------

    def _most_common_duration(self, rows: list[dict]) -> int:
        durations = []
        for r in rows:
            if r["start_min"] is not None and r["end_min"] is not None:
                durations.append(r["end_min"] - r["start_min"])
        if not durations:
            return 60  # default 1 hour
        return max(set(durations), key=durations.count)

    def _most_common_aula(self, rows: list[dict]) -> str | None:
        aulas = [r["aula"] for r in rows if r["aula"]]
        if not aulas:
            return None
        return max(set(aulas), key=aulas.count)

    def _most_common_day(self, rows: list[dict]) -> str | None:
        days = [d for r in rows for d in r["days"]]
        if not days:
            return None
        return max(set(days), key=days.count)

    def _most_common_start(self, rows: list[dict]) -> int | None:
        starts = [r["start_min"] for r in rows if r["start_min"] is not None]
        if not starts:
            return None
        return max(set(starts), key=starts.count)
