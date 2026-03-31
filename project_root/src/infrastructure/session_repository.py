# src/infrastructure/session_repository.py

import json
import sqlite3
from pathlib import Path

from ..scheduling.classroom import Classroom
from ..scheduling.course import Course


class SessionRepository:
    """
    Persists and restores a SORTH working session using SQLite.

    Stores: classrooms, courses (with per-group suggestions), classroom
    restrictions, the last generated schedule (assignments), and session
    metadata (excel path, seed).

    The database is a single file: data/sorth_session.db
    """

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            import sys
            if getattr(sys, 'frozen', False):
                # Running as .exe: save next to the executable
                base = Path(sys.executable).parent / "data"
            else:
                base = Path(__file__).parent.parent.parent / "data"
            base.mkdir(exist_ok=True)
            db_path = str(base / "sorth_session.db")
        self._db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self):
        with self._connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS session (
                    id          INTEGER PRIMARY KEY CHECK (id = 1),
                    excel_path  TEXT,
                    seed        INTEGER,
                    saved_at    TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS classrooms (
                    name        TEXT PRIMARY KEY,
                    capacity    INTEGER NOT NULL,
                    room_type   TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    campus      TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS courses (
                    code                TEXT PRIMARY KEY,
                    name                TEXT,
                    number_of_groups    INTEGER NOT NULL,
                    duration_min        INTEGER NOT NULL,
                    required_room_type  TEXT NOT NULL,
                    suggested_classroom TEXT,
                    preferred_day       TEXT,
                    preferred_start_min INTEGER,
                    force_split         INTEGER  -- NULL=auto, 1=force, 0=never
                );

                CREATE TABLE IF NOT EXISTS course_group_suggestions (
                    course_code         TEXT NOT NULL,
                    group_index         INTEGER NOT NULL,
                    aula                TEXT,
                    preferred_day       TEXT,
                    preferred_start_min INTEGER,
                    PRIMARY KEY (course_code, group_index)
                );

                CREATE TABLE IF NOT EXISTS restrictions (
                    classroom_name  TEXT NOT NULL,
                    course_code     TEXT NOT NULL,
                    PRIMARY KEY (classroom_name, course_code)
                );

                CREATE TABLE IF NOT EXISTS assignments (
                    group_id        TEXT PRIMARY KEY,
                    classroom_name  TEXT NOT NULL,
                    day             INTEGER NOT NULL,
                    start_min       INTEGER NOT NULL,
                    end_min         INTEGER NOT NULL
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self._db_path)
        con.row_factory = sqlite3.Row
        return con

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save_session(self, excel_path: str | None, seed: int | None,
                     classrooms: dict[str, Classroom],
                     courses: list[Course],
                     restrictions: dict[str, set[str]],
                     assignments: dict | None):
        with self._connect() as con:
            # Session metadata
            con.execute("""
                INSERT INTO session (id, excel_path, seed, saved_at)
                VALUES (1, ?, ?, datetime('now'))
                ON CONFLICT(id) DO UPDATE SET
                    excel_path = excluded.excel_path,
                    seed       = excluded.seed,
                    saved_at   = excluded.saved_at
            """, (excel_path, seed))

            # Classrooms
            con.execute("DELETE FROM classrooms")
            con.executemany("""
                INSERT INTO classrooms (name, capacity, room_type, description, campus)
                VALUES (?, ?, ?, ?, ?)
            """, [(c.name, c.capacity, c.room_type, c.description, c.campus)
                  for c in classrooms.values()])

            # Courses + per-group suggestions
            con.execute("DELETE FROM courses")
            con.execute("DELETE FROM course_group_suggestions")
            for course in courses:
                fs = None if course.force_split is None else (1 if course.force_split else 0)
                con.execute("""
                    INSERT INTO courses
                        (code, name, number_of_groups, duration_min, required_room_type,
                         suggested_classroom, preferred_day, preferred_start_min, force_split)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (course.code, course.name, course.number_of_groups,
                      course.duration_min, course.required_room_type,
                      course.suggested_classroom, course.preferred_day,
                      course.preferred_start_min, fs))
                for idx, sg in enumerate(course.group_suggestions):
                    con.execute("""
                        INSERT INTO course_group_suggestions
                            (course_code, group_index, aula, preferred_day, preferred_start_min)
                        VALUES (?, ?, ?, ?, ?)
                    """, (course.code, idx,
                          sg.get("aula"), sg.get("preferred_day"),
                          sg.get("preferred_start_min")))

            # Restrictions
            con.execute("DELETE FROM restrictions")
            for cls_name, codes in restrictions.items():
                con.executemany("""
                    INSERT INTO restrictions (classroom_name, course_code) VALUES (?, ?)
                """, [(cls_name, code) for code in codes])

            # Assignments
            con.execute("DELETE FROM assignments")
            if assignments:
                con.executemany("""
                    INSERT INTO assignments
                        (group_id, classroom_name, day, start_min, end_min)
                    VALUES (?, ?, ?, ?, ?)
                """, [(gid, cls, day, s, e)
                      for gid, (cls, day, s, e) in assignments.items()])

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_session(self) -> dict | None:
        """
        Returns a dict with keys:
            excel_path, seed, classrooms, courses, restrictions, assignments
        or None if no session exists.
        """
        with self._connect() as con:
            row = con.execute("SELECT * FROM session WHERE id = 1").fetchone()
            if not row:
                return None

            # Classrooms
            classrooms = {}
            for r in con.execute("SELECT * FROM classrooms"):
                c = Classroom(r["name"], r["capacity"], r["room_type"],
                              r["description"], r["campus"])
                classrooms[c.name] = c

            # Per-group suggestions grouped by course
            suggestions_by_code: dict[str, list] = {}
            for r in con.execute(
                "SELECT * FROM course_group_suggestions ORDER BY course_code, group_index"
            ):
                suggestions_by_code.setdefault(r["course_code"], []).append({
                    "aula":                r["aula"],
                    "preferred_day":       r["preferred_day"],
                    "preferred_start_min": r["preferred_start_min"],
                })

            # Courses
            courses = []
            for r in con.execute("SELECT * FROM courses"):
                fs_raw = r["force_split"]
                force_split = None if fs_raw is None else bool(fs_raw)
                courses.append(Course(
                    code=r["code"],
                    name=r["name"],
                    number_of_groups=r["number_of_groups"],
                    duration_min=r["duration_min"],
                    required_room_type=r["required_room_type"],
                    suggested_classroom=r["suggested_classroom"],
                    preferred_day=r["preferred_day"],
                    preferred_start_min=r["preferred_start_min"],
                    force_split=force_split,
                    group_suggestions=suggestions_by_code.get(r["code"], []),
                ))

            # Restrictions
            restrictions: dict[str, set[str]] = {}
            for r in con.execute("SELECT * FROM restrictions"):
                restrictions.setdefault(r["classroom_name"], set()).add(r["course_code"])

            # Assignments
            assignments = {}
            for r in con.execute("SELECT * FROM assignments"):
                assignments[r["group_id"]] = (
                    r["classroom_name"], r["day"], r["start_min"], r["end_min"]
                )

            return {
                "excel_path":   row["excel_path"],
                "seed":         row["seed"],
                "classrooms":   classrooms,
                "courses":      courses,
                "restrictions": restrictions,
                "assignments":  assignments if assignments else None,
            }

    def has_session(self) -> bool:
        """Returns True only if there is a saved session with courses."""
        with self._connect() as con:
            row = con.execute("SELECT id FROM session WHERE id = 1").fetchone()
            if not row:
                return False
            return con.execute("SELECT COUNT(*) FROM courses").fetchone()[0] > 0

    def get_course_completions(self) -> list[tuple[str, str]]:
        """Return list of (code, name) for all saved courses, for autocomplete."""
        with self._connect() as con:
            rows = con.execute("SELECT code, name FROM courses ORDER BY code").fetchall()
            return [(r["code"], r["name"] or "") for r in rows]

    def clear_session(self):
        with self._connect() as con:
            con.executescript("""
                DELETE FROM assignments;
                DELETE FROM restrictions;
                DELETE FROM course_group_suggestions;
                DELETE FROM courses;
                DELETE FROM classrooms;
                DELETE FROM session;
            """)
