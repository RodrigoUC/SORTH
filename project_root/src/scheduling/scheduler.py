from random import Random
from typing import List
from .schedule_state import ScheduleState
from .group import Group
from .time_model import TimeModel


class Scheduler:

    def __init__(self, seed: int | None = 42):
        self._rng = Random(seed)
        self._all_groups: List[Group] = []

    def schedule(self, state: ScheduleState, groups: List[Group]) -> bool:
        self._all_groups = groups
        self._initialize_domains(state, groups)
        groups.sort(key=lambda g: len(g.domain))
        return self._backtrack(state, groups)

    # ------------------------------------------------------------------
    # Domain initialization
    # ------------------------------------------------------------------

    def _initialize_domains(self, state: ScheduleState, groups: List[Group]):
        for group in groups:
            domain = []

            for classroom in state.classrooms.values():
                if classroom.room_type != group.required_room_type:
                    continue
                if classroom.capacity < group.size:
                    continue
                # Classroom course restriction
                if group.course_code and not classroom.allows_course(group.course_code):
                    continue

                for day in range(1, state.time_model.days_count + 1):
                    # Respect preferred day if set
                    if group.preferred_day:
                        day_name = state.time_model.to_day_name(day)
                        if day_name != group.preferred_day:
                            continue

                    start_candidates = state.time_model.generate_start_candidates(
                        group.duration_min,
                        group.preferred_start_min
                    )

                    for start_min in start_candidates:
                        end_min = start_min + group.duration_min
                        if classroom.is_available(day, start_min, end_min):
                            domain.append((classroom, day, start_min))

            group.domain = domain

    # ------------------------------------------------------------------
    # Backtracking
    # ------------------------------------------------------------------

    def _backtrack(self, state: ScheduleState, groups: List[Group]) -> bool:
        unassigned = [g for g in groups if not g.is_assigned()]

        if not unassigned:
            return True

        # MRV: pick group with smallest domain
        group = min(unassigned, key=lambda g: len(g.domain))

        domain_candidates = list(group.domain)
        self._rng.shuffle(domain_candidates)

        # For subgroups: try parent classroom first
        if group.parent_group_id:
            parent_classroom = self._get_parent_classroom(group.parent_group_id)
            if parent_classroom:
                parent_cands = [a for a in domain_candidates if a[0].name == parent_classroom]
                other_cands  = [a for a in domain_candidates if a[0].name != parent_classroom]
                ordered = (self._sort_assignments(state, group, parent_cands) +
                           self._sort_assignments(state, group, other_cands))
            else:
                ordered = self._sort_assignments(state, group, domain_candidates)
        else:
            ordered = self._sort_assignments(state, group, domain_candidates)

        for classroom, day, start_min in ordered:
            if state.assign(group, classroom.name, day, start_min):

                if group.parent_group_id and not self._is_valid_subgroup(state, group, day, start_min):
                    state.unassign(group)
                    continue

                removed = self._forward_check(state, group, unassigned)

                if removed is not None and self._backtrack(state, groups):
                    return True

                self._restore_domains(removed)
                state.unassign(group)

        return False

    # ------------------------------------------------------------------
    # Sorting / heuristics
    # ------------------------------------------------------------------

    def _sort_assignments(self, state: ScheduleState, group: Group, candidates: list) -> list:
        return sorted(
            candidates,
            key=lambda a: (
                self._preference_score(state, group, a[1], a[2]),
                self._day_score(state, a[1]),
                self._time_score(state, a[2]),
                self._classroom_load(state, a[0].name),
                self._classroom_usage(state, a[0].name),
                -self._estimate_impact(state, group, a, []),
            )
        )

    def _preference_score(self, state: ScheduleState, group: Group,
                          day: int, start_min: int) -> int:
        """0=both match, 1=day only, 2=hour only, 3=no match / no preference."""
        if not group.preferred_day and group.preferred_start_min is None:
            return 3

        day_match = True
        if group.preferred_day:
            day_match = state.time_model.to_day_name(day) == group.preferred_day

        hour_match = True
        if group.preferred_start_min is not None:
            hour_match = start_min == group.preferred_start_min

        if day_match and hour_match:
            return 0
        if day_match:
            return 1
        if hour_match:
            return 2
        return 3

    def _day_score(self, state: ScheduleState, day: int) -> int:
        day_name = state.time_model.to_day_name(day)
        day_load = sum(1 for _, d, _, _ in state.assignments.values() if d == day)
        weekdays = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        if day_name in weekdays:
            return day_load if day_load <= 2 else 500 + day_load
        return 50 + day_load

    def _time_score(self, state: ScheduleState, start_min: int) -> int:
        hour_load = sum(
            1 for _, _, s, _ in state.assignments.values()
            if s == start_min
        )
        if start_min <= 16 * 60:
            return hour_load
        return 100 + (start_min - 16 * 60) // 60

    def _classroom_load(self, state: ScheduleState, classroom_name: str) -> int:
        """Total minutes assigned to a classroom."""
        durations = {g.group_id: g.duration_min for g in self._all_groups}
        return sum(
            durations.get(gid, 0)
            for gid, (cls, _, _, _) in state.assignments.items()
            if cls == classroom_name
        )

    def _classroom_usage(self, state: ScheduleState, classroom_name: str) -> int:
        return sum(1 for cls, _, _, _ in state.assignments.values() if cls == classroom_name)

    # ------------------------------------------------------------------
    # Forward checking
    # ------------------------------------------------------------------

    def _forward_check(self, state: ScheduleState, assigned_group: Group,
                       unassigned: list) -> dict | None:
        removed = {}

        for other in unassigned:
            if other == assigned_group:
                continue

            to_remove = []
            for assignment in other.domain:
                classroom, day, start_min = assignment
                end_min = start_min + other.duration_min

                if not state.classrooms[classroom.name].is_available(day, start_min, end_min):
                    to_remove.append(assignment)
                elif other.parent_group_id:
                    if not self._is_valid_subgroup(state, other, day, start_min):
                        to_remove.append(assignment)

            if to_remove:
                removed[other.group_id] = to_remove
                for a in to_remove:
                    other.domain.remove(a)

                if not other.domain:
                    self._restore_domains(removed)
                    return None

        return removed

    # ------------------------------------------------------------------
    # Subgroup constraints
    # ------------------------------------------------------------------

    def _get_parent_classroom(self, parent_group_id: str) -> str | None:
        for g in self._all_groups:
            if g.parent_group_id == parent_group_id and g.is_assigned():
                return g.assignment[0]
        return None

    def _is_valid_subgroup(self, state: ScheduleState, subgroup: Group,
                           day: int, start_min: int) -> bool:
        """Subgroups of same parent must be on different days at the same start time."""
        parent_id = subgroup.parent_group_id
        if not parent_id:
            return True

        for other in self._all_groups:
            if other.parent_group_id != parent_id or other is subgroup:
                continue
            if not other.is_assigned():
                continue

            _, other_day, other_start, _ = other.assignment

            if other_day == day:
                return False
            if other_start != start_min:
                return False

        return True

    # ------------------------------------------------------------------
    # Domain restore
    # ------------------------------------------------------------------

    def _restore_domains(self, removed: dict | None):
        if not removed:
            return
        for group_id, assignments in removed.items():
            for g in self._all_groups:
                if g.group_id == group_id:
                    g.domain.extend(assignments)
                    break

    # ------------------------------------------------------------------
    # LCV impact estimate
    # ------------------------------------------------------------------

    def _estimate_impact(self, state: ScheduleState, group: Group,
                         assignment: tuple, unassigned: list) -> int:
        classroom, day, start_min = assignment
        state.assign(group, classroom.name, day, start_min)
        impact = sum(len(o.domain) for o in unassigned if o is not group)
        state.unassign(group)
        return impact
