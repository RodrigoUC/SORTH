# src/scheduling/group.py

class Group:

    def __init__(
        self,
        group_id: str,
        duration: int,
        required_room_type: str,
        size: int = 0,
        suggested_classroom: str | None = None,
        course_code: str | None = None
    ):
        self.group_id = group_id
        self.duration = duration
        self.required_room_type = required_room_type
        self.size = size
        self.suggested_classroom = suggested_classroom
        self.course_code = course_code

        self.assignment = None
        self.domain = []

    def is_assigned(self) -> bool:
        return self.assignment is not None