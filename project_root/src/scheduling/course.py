# src/scheduling/course.py

from .group import Group


class Course:

    def __init__(
        self,
        code: str,
        number_of_groups: int,
        duration: int,
        required_room_type: str,
        suggested_classroom: str | None = None
    ):
        self.code = code
        self.number_of_groups = number_of_groups
        self.duration = duration
        self.required_room_type = required_room_type
        self.suggested_classroom = suggested_classroom

    def generate_groups(self) -> list[Group]:
        groups = []

        for i in range(1, self.number_of_groups + 1):
            groups.append(
                Group(
                    group_id=f"{self.code}-G{i}",
                    duration=self.duration,
                    required_room_type=self.required_room_type,
                    suggested_classroom=self.suggested_classroom,
                    course_code=self.code
                )
            )

        return groups