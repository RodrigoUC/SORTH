from typing import List, Optional
from .group import Group


class Course:

    def __init__(
        self,
        code: str,
        number_of_groups: int,
        duration: int,
        required_room_type: str,
        suggested_classroom: Optional[str] = None
    ):
        self.code = code
        self.number_of_groups = number_of_groups
        self.duration = duration
        self.required_room_type = required_room_type
        self.suggested_classroom = suggested_classroom

    def generate_groups(self) -> List[Group]:
        groups = []

        for i in range(1, self.number_of_groups + 1):
            group_id = f"{self.code}-G{i}"

            group = Group(
                group_id=group_id,
                course_code=self.code,
                duration=self.duration,
                required_room_type=self.required_room_type,
                suggested_classroom=self.suggested_classroom
            )

            groups.append(group)

        return groups