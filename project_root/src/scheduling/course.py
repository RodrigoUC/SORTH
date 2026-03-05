# src/scheduling/course.py

from .group import Group


class Course:

    def __init__(
        self,
        code: str,
        number_of_groups: int,
        duration: int,
        required_room_type: str,
        suggested_classroom: str | None = None,
        preferred_day: str | None = None,
        preferred_hour: int | None = None,
        name: str | None = None
    ):
        self.code = code
        self.name = name
        self.number_of_groups = number_of_groups
        self.duration = duration
        self.required_room_type = required_room_type
        self.suggested_classroom = suggested_classroom
        self.preferred_day = preferred_day
        self.preferred_hour = preferred_hour

    def generate_groups(self) -> list[Group]:
        groups = []

        for i in range(1, self.number_of_groups + 1):
            base_group_id = f"{self.code}-G{i}"
            
            # Check if duration needs to be split (> 3 blocks)
            if self.duration <= 3:
                # Single group - no splitting needed
                groups.append(
                    Group(
                        group_id=base_group_id,
                        duration=self.duration,
                        required_room_type=self.required_room_type,
                        suggested_classroom=self.suggested_classroom,
                        course_code=self.code,
                        preferred_day=self.preferred_day,
                        preferred_hour=self.preferred_hour,
                        course_name=self.name
                    )
                )
            else:
                # Split into multiple subgroups across different days
                subgroups = self._split_duration(self.duration)
                
                for subgroup_idx, sub_duration in enumerate(subgroups, 1):
                    subgroup_id = f"{base_group_id}-P{subgroup_idx}"
                    groups.append(
                        Group(
                            group_id=subgroup_id,
                            duration=sub_duration,
                            required_room_type=self.required_room_type,
                            suggested_classroom=self.suggested_classroom,
                            course_code=self.code,
                            preferred_day=self.preferred_day,
                            preferred_hour=self.preferred_hour,
                            course_name=self.name,
                            parent_group_id=base_group_id,
                            subgroup_index=subgroup_idx,
                            total_subgroups=len(subgroups)
                        )
                    )

        return groups
    
    def _split_duration(self, duration: int) -> list[int]:
        """
        Split a large duration into multiple parts for different days.
        Target: 2 blocks per day (except when necessary to use 3)
        
        Examples:
        - 4 blocks → [2, 2]
        - 5 blocks → [2, 3]
        - 6 blocks → [2, 2, 2]
        - 7 blocks → [2, 2, 3]
        - 8 blocks → [2, 2, 2, 2]
        - 9 blocks → [2, 2, 2, 3]
        """
        if duration <= 3:
            return [duration]
        
        # Prefer 2-block chunks as much as possible
        if duration % 2 == 0:
            # Even: use all 2-block chunks
            return [2] * (duration // 2)
        else:
            # Odd: use 2-block chunks and one 3-block chunk
            num_2blocks = (duration - 3) // 2
            return [2] * num_2blocks + [3]