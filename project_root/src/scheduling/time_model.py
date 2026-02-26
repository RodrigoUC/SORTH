class TimeModel:

    def __init__(self, days: list[str], hours: list[int]):
        self.days = sorted(days)
        self.hours = sorted(hours)

        self.day_to_index = {d: i + 1 for i, d in enumerate(self.days)}
        self.index_to_day = {i + 1: d for i, d in enumerate(self.days)}

        self.hour_to_index = {h: i + 1 for i, h in enumerate(self.hours)}
        self.index_to_hour = {i + 1: h for i, h in enumerate(self.hours)}

        self.days_count = len(self.days)
        self.blocks_per_day = len(self.hours)

    def is_valid_slot(self, day: int, start_block: int, duration: int) -> bool:
        if day < 1 or day > self.days_count:
            return False

        if start_block < 1:
            return False

        end_block = start_block + duration - 1

        if end_block > self.blocks_per_day:
            return False

        return True

    def to_internal(self, day: str, hour: int) -> tuple[int, int]:
        return (
            self.day_to_index[day],
            self.hour_to_index[hour]
        )

    def to_external(self, day_index: int, block_index: int) -> tuple[str, int]:
        return (
            self.index_to_day[day_index],
            self.index_to_hour[block_index]
        )

    @classmethod
    def from_availability(cls, availability: dict):
        days = set()
        hours = set()

        for (_, day, hour), _ in availability.items():
            days.add(day)
            hours.add(hour)

        return cls(sorted(days), sorted(hours))