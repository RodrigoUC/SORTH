# src/scheduling/scheduler.py

from typing import List
from .schedule_state import ScheduleState
from .group import Group


class Scheduler:

    def schedule(self, state: ScheduleState, groups: List[Group]) -> bool:
        self._all_groups = groups
        self._initialize_domains(state, groups)

        # Orden inicial por MRV (menos opciones primero)
        groups.sort(key=lambda g: len(g.domain))

        return self._backtrack(state, groups)

    def _initialize_domains(self, state: ScheduleState, groups: List[Group]):

        for group in groups:
            domain = []

            for classroom in state.classrooms.values():

                if classroom.room_type != group.required_room_type:
                    continue

                if classroom.capacity < group.size:
                    continue

                max_start = state.time_model.blocks_per_day - group.duration + 1

                for day in range(1, state.time_model.days_count + 1):
                    for block in range(1, max_start + 1):

                        if classroom.is_available(day, block, group.duration):
                            domain.append((classroom, day, block))

            group.domain = domain

    def _backtrack(self, state: ScheduleState, groups: List[Group]) -> bool:

        unassigned = [g for g in groups if not g.is_assigned()]

        if not unassigned:
            return True

        # MRV dinámico
        group = min(unassigned, key=lambda g: len(g.domain))

        # LCV ligero: ordenar por menor impacto estimado
        ordered_domain = sorted(
            group.domain,
            key=lambda assignment: self._estimate_impact(state, group, assignment, unassigned),
            reverse=True
        )

        for classroom, day, block in ordered_domain:

            if state.assign(group, classroom.name, day, block):

                removed = self._forward_check(state, group, unassigned)

                self._all_groups = groups
                if removed is not None and self._backtrack(state, groups):
                    return True

                self._restore_domains(removed)
                state.unassign(group)

        return False

    def _forward_check(self, state, assigned_group, unassigned):

        removed = {}

        for other in unassigned:

            if other == assigned_group:
                continue

            to_remove = []

            for assignment in other.domain:
                classroom, day, block = assignment

                if not state.classrooms[classroom.name].is_available(
                    day, block, other.duration
                ):
                    to_remove.append(assignment)

            if to_remove:
                removed[other.group_id] = to_remove
                for assignment in to_remove:
                    other.domain.remove(assignment)

                if not other.domain:
                    self._restore_domains(removed)
                    return None

        return removed

    def _restore_domains(self, removed):

        if not removed:
            return

        for group_id, assignments in removed.items():
            for group in self._all_groups:
                if group.group_id == group_id:
                    group.domain.extend(assignments)

    def _estimate_impact(self, state, group, assignment, unassigned):

        classroom, day, block = assignment

        state.assign(group, classroom.name, day, block)

        impact = 0
        for other in unassigned:
            if other == group:
                continue
            impact += len(other.domain)

        state.unassign(group)

        return impact