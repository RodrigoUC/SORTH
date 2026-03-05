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
        preferred_hour: int | None = None,
        course_name: str | None = None,
        parent_group_id: str | None = None,
        subgroup_index: int = 0,
        total_subgroups: int = 1
    ):
        self.group_id = group_id
        self.duration = duration
        self.required_room_type = required_room_type
        self.size = size
        self.suggested_classroom = suggested_classroom
        self.course_code = course_code
        self.course_name = course_name
        self.preferred_day = preferred_day
        self.preferred_hour = preferred_hour
        
        # For split groups (durations > 3)
        self.parent_group_id = parent_group_id
        self.subgroup_index = subgroup_index
        self.total_subgroups = total_subgroups

        self.assignment = None
        self.domain = []

    def is_assigned(self) -> bool:
        return self.assignment is not None