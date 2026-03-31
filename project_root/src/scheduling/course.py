from .group import Group

# Sessions longer than this are split across multiple days
SPLIT_THRESHOLD_MIN = 180  # 3 hours


class Course:

    def __init__(
        self,
        code: str,
        number_of_groups: int,
        duration_min: int,
        required_room_type: str,
        size: int = 0,
        suggested_classroom: str | None = None,
        preferred_day: str | None = None,
        preferred_start_min: int | None = None,
        name: str | None = None,
    ):
        self.code = code
        self.name = name
        self.number_of_groups = number_of_groups
        self.duration_min = duration_min
        self.required_room_type = required_room_type
        self.size = size
        self.suggested_classroom = suggested_classroom
        self.preferred_day = preferred_day
        self.preferred_start_min = preferred_start_min

    def generate_groups(self) -> list[Group]:
        groups = []

        for i in range(1, self.number_of_groups + 1):
            base_group_id = f"{self.code}-G{i}"

            if self.duration_min <= SPLIT_THRESHOLD_MIN:
                groups.append(Group(
                    group_id=base_group_id,
                    duration_min=self.duration_min,
                    required_room_type=self.required_room_type,
                    size=self.size,
                    suggested_classroom=self.suggested_classroom,
                    course_code=self.code,
                    preferred_start_min=self.preferred_start_min,
                    preferred_day=self.preferred_day,
                    course_name=self.name,
                ))
            else:
                parts = self._split_duration(self.duration_min)
                for idx, part_min in enumerate(parts, 1):
                    groups.append(Group(
                        group_id=f"{base_group_id}-P{idx}",
                        duration_min=part_min,
                        required_room_type=self.required_room_type,
                        size=self.size,
                        suggested_classroom=self.suggested_classroom,
                        course_code=self.code,
                        preferred_start_min=self.preferred_start_min,
                        preferred_day=self.preferred_day,
                        course_name=self.name,
                        parent_group_id=base_group_id,
                        subgroup_index=idx,
                        total_subgroups=len(parts),
                    ))

        return groups

    def _split_duration(self, duration_min: int) -> list[int]:
        """
        Split a long session into parts of at most SPLIT_THRESHOLD_MIN minutes.
        Prefer equal-sized chunks of 120 min (2h), last chunk gets the remainder.

        Examples:
          240 min → [120, 120]
          300 min → [120, 120, 60]
          360 min → [120, 120, 120]
        """
        chunk = 120  # preferred chunk size in minutes
        parts = []
        remaining = duration_min
        while remaining > chunk:
            parts.append(chunk)
            remaining -= chunk
        parts.append(remaining)
        return parts
