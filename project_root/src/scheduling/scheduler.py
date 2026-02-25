from typing import List
from .schedule_state import ScheduleState
from .group import Group


class Scheduler:

    def schedule(self, state: ScheduleState, groups: List[Group]) -> bool:
        return self._backtrack(state, groups)
    
    def _backtrack(self, state: ScheduleState, groups: List[Group]) -> bool:

        unassigned = [g for g in groups if not g.is_assigned()]

        if not unassigned:
            return True

        # Compute domain size for each group
        def count_possible_assignments(group: Group) -> int:
            count = 0

            possible_classrooms = [
                c for c in state.classrooms.values()
                if c.room_type == group.required_room_type
            ]

            max_start = state.time_model.blocks_per_day - group.duration + 1

            for classroom in possible_classrooms:
                for day in range(1, state.time_model.days + 1):
                    for block in range(1, max_start + 1):
                        if state.time_model.is_valid_slot(day, block, group.duration) \
                        and classroom.is_available(day, block, group.duration):
                            count += 1

            return count

        # Select group with minimum remaining values
        group = min(unassigned, key=count_possible_assignments)

        possible_classrooms = [
            c for c in state.classrooms.values()
            if c.room_type == group.required_room_type
        ]

        max_start = state.time_model.blocks_per_day - group.duration + 1

        for classroom in possible_classrooms:
            for day in range(1, state.time_model.days + 1):
                for block in range(1, max_start + 1):

                    if state.assign(group, classroom.name, day, block):

                        if self._backtrack(state, groups):
                            return True

                        state.unassign(group)

        return False