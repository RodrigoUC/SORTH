# src/scheduling/scheduler.py

from random import Random
from typing import List
from .schedule_state import ScheduleState
from .group import Group


class Scheduler:

    def __init__(self, seed: int | None = 42):
        # Default fixed seed for reproducible results.
        # Use seed=None if you want different results in each execution.
        self._rng = Random(seed)
        self._all_groups = []

    def schedule(self, state: ScheduleState, groups: List[Group]) -> bool:
        self._all_groups = groups
        self._initialize_domains(state, groups)

        # Initial order by MRV (minimum remaining values)
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

                        # Skip lunch hour (12:00) - check if any block overlaps with lunch
                        overlaps_lunch = False
                        for offset in range(group.duration):
                            hour = state.time_model.index_to_hour.get(block + offset)
                            if hour == 12:
                                overlaps_lunch = True
                                break
                        
                        if overlaps_lunch:
                            continue  # Do not add to domain

                        if classroom.is_available(day, block, group.duration):
                            domain.append((classroom, day, block))

            group.domain = domain

    def _backtrack(self, state: ScheduleState, groups: List[Group]) -> bool:

        unassigned = [g for g in groups if not g.is_assigned()]

        if not unassigned:
            return True

        # MRV dinámico
        group = min(unassigned, key=lambda g: len(g.domain))

        # Aleatoriedad controlada para desempates
        domain_candidates = list(group.domain)
        self._rng.shuffle(domain_candidates)

        # LCV + classroom balance by actual load (blocks):
        # 1) specific group preferences (day and hour)
        # 2) prefer weekdays Monday to Friday
        # 3) prefer schedules until 16:00
        # 4) lower total load in blocks
        # 5) fewer number of groups
        # 6) higher feasibility (light LCV)
        ordered_domain = sorted(
            domain_candidates,
            key=lambda assignment: (
                self._preference_score(state, group, assignment[1], assignment[2]),
                self._day_preference_score(state, assignment[1]),
                self._time_preference_score(state, assignment[2]),
                self._classroom_load_blocks(state, assignment[0].name),
                self._classroom_usage(state, assignment[0].name),
                -self._estimate_impact(state, group, assignment, unassigned),
            )
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

    def _preference_score(self, state: ScheduleState, group: Group, day: int, start_block: int) -> int:
        """
        Calculate score based on group-specific preferences.
        Lower score = matches preferences
        Higher score = does not match preferences
        
        Returns:
            0 - Matches both preferred day and hour
            1 - Matches preferred day only
            2 - Matches preferred hour only  
            3 - Does not match any preference or no preferences set
        """
        # If no preferences, neutral score
        if not group.preferred_day and not group.preferred_hour:
            return 3
        
        day_match = False
        hour_match = False
        
        # Check day match
        if group.preferred_day:
            day_name = state.time_model.index_to_day.get(day)
            day_match = (day_name == group.preferred_day)
        else:
            day_match = True  # No preference, consider as match
        
        # Check hour match
        if group.preferred_hour:
            hour = state.time_model.index_to_hour.get(start_block)
            hour_match = (hour == group.preferred_hour)
        else:
            hour_match = True  # No preference, consider as match
        
        # Calculate score
        if day_match and hour_match:
            return 0  # Matches everything
        elif day_match:
            return 1  # Day only
        elif hour_match:
            return 2  # Hour only
        else:
            return 3  # No match

    def _classroom_usage(self, state: ScheduleState, classroom_name: str) -> int:
        """Number of groups already assigned to a classroom."""
        return sum(
            1 for assigned in state.assignments.values()
            if assigned[0] == classroom_name
        )

    def _day_preference_score(self, state: ScheduleState, day: int) -> int:
        """
        Calculate day of week preference score.
        Lower score = more preferred (with equitable distribution)
        Higher score = less preferred (overloaded days)
        
        Favors:
        - Equitable distribution between Monday to Friday
        - Days with fewer classes assigned
        - Limits to maximum 2 groups per day (heavily penalizes 3+)
        - Saturday is acceptable but with lower priority
        """
        day_name = state.time_model.index_to_day.get(day)
        
        if day_name is None:
            return 1000
        
        # Count how many classes are already assigned to this day
        day_load = sum(
            1 for _, (_, assigned_day, _) in state.assignments.items()
            if assigned_day == day
        )
        
        weekdays = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        
        # High priority: Monday to Friday
        if day_name in weekdays:
            # Allow 1-2 groups (low score)
            if day_load <= 2:
                return day_load
            # Heavily penalize more than 3 groups
            else:
                return 500 + day_load
        
        # Medium priority: Saturday (acceptable but after weekdays)
        else:
            return 50 + day_load  # Lower penalty, still usable
    
    def _time_preference_score(self, state: ScheduleState, start_block: int) -> int:
        """
        Calculate time slot preference score.
        Lower score = more preferred
        Higher score = less preferred
        
        Prioritizes:
        - Time slots until 16:00 (with equitable distribution)
        - Avoids time slots after 16:00
        
        Note: 12:00 (lunch hour) is completely excluded from domain initialization
        """
        # Get actual hour of the block
        hour = state.time_model.index_to_hour.get(start_block)
        
        if hour is None:
            return 1000  # High penalty if hour not found
        
        # Count how many classes are already assigned to this time block
        hour_load = sum(
            1 for _, (_, _, assigned_block) in state.assignments.items()
            if assigned_block == start_block
        )
        
        # High priority: Until 16:00 (equitable distribution by load)
        if hour <= 16:
            return hour_load  # Favors time slots with fewer classes
        
        # Low priority: After 16:00
        else:
            return 100 + (hour - 16)  # High score to discourage


    def _classroom_load_blocks(self, state: ScheduleState, classroom_name: str) -> int:
        """Total classroom load in blocks (considers duration of each group)."""
        durations = {g.group_id: g.duration for g in self._all_groups}
        load = 0

        for group_id, (assigned_classroom, _, _) in state.assignments.items():
            if assigned_classroom == classroom_name:
                load += durations.get(group_id, 0)

        return load

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