# src/scheduling/group.py

class Group:

    def __init__(
        self,
        group_id: str,
        duration: int,
        required_room_type: str,
        size: int = 0,
        suggested_classroom: str | None = None,
        course_code: str | None = None,
        preferred_day: str | None = None,
        preferred_hour: int | None = None
    ):
        self.group_id = group_id
        self.duration = duration
        self.required_room_type = required_room_type
        self.size = size
        self.suggested_classroom = suggested_classroom
        self.course_code = course_code
        self.preferred_day = preferred_day
        self.preferred_hour = preferred_hour

        self.assignment = None
        self.domain = []

    def is_assigned(self) -> bool:
        return self.assignment is not None