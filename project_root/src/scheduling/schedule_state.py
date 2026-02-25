from typing import List
from .time_model import TimeModel
from .classroom import Classroom
from .group import Group


class ScheduleState:

    def __init__(self, time_model: TimeModel, classrooms: List[Classroom]):
        self.time_model = time_model
        self.classrooms = {c.name: c for c in classrooms}
        self.assignments = {}

    def assign(self, group: Group, classroom_name: str, day: int, start_block: int) -> bool:

        if classroom_name not in self.classrooms:
            return False

        classroom = self.classrooms[classroom_name]

        if classroom.room_type != group.required_room_type:
            return False

        if not self.time_model.is_valid_slot(day, start_block, group.duration):
            return False

        if not classroom.is_available(day, start_block, group.duration):
            return False

        classroom.occupy(day, start_block, group.duration)

        group.assignment = (classroom_name, day, start_block)

        self.assignments[group.group_id] = group.assignment

        return True

    def unassign(self, group: Group) -> None:
        if group.group_id not in self.assignments:
            return

        classroom_name, day, start_block = self.assignments[group.group_id]

        classroom = self.classrooms[classroom_name]

        classroom.release(day, start_block, group.duration)

        group.assignment = None
        del self.assignments[group.group_id]