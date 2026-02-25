from typing import List
from .schedule_state import ScheduleState
from .group import Group


class Scheduler:

    def schedule(self, state: ScheduleState, groups: List[Group]) -> bool:

        def difficulty(group: Group):
            room_constraint = 0 if group.required_room_type == "Laboratory" else 1
            return (room_constraint, -group.duration)

        groups_sorted = sorted(groups, key=difficulty)

        return self._backtrack(state, groups_sorted, 0)

    def _backtrack(self, state: ScheduleState, groups: List[Group], index: int) -> bool:
        if index >= len(groups):
            return True

        group = groups[index]

        possible_classrooms = [
            c for c in state.classrooms.values()
            if c.room_type == group.required_room_type
        ]

        for classroom in possible_classrooms:

            for day in range(1, state.time_model.days + 1):
                max_start = state.time_model.blocks_per_day - group.duration + 1
                for block in range(1, max_start + 1):

                    if state.assign(group, classroom.name, day, block):

                        if self._backtrack(state, groups, index + 1):
                            return True

                        state.unassign(group)

        return False