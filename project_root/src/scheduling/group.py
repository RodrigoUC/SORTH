from typing import Optional


class Group:

    def __init__(
        self,
        group_id: str,
        course_code: str,
        duration: int,
        required_room_type: str,
        suggested_classroom: Optional[str] = None
    ):
        self.group_id = group_id
        self.course_code = course_code
        self.duration = duration
        self.required_room_type = required_room_type
        self.suggested_classroom = suggested_classroom
        self.assignment = None

    def is_assigned(self) -> bool:
        return self.assignment is not None