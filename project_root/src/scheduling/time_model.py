class TimeModel:

    def __init__(self, days: int, blocks_per_day: int):
        self.days = days
        self.blocks_per_day = blocks_per_day

    def is_valid_slot(self, day: int, start_block: int, duration: int) -> bool:
        if day < 1 or day > self.days:
            return False

        if start_block < 1:
            return False

        end_block = start_block + duration - 1

        if end_block >= self.blocks_per_day:
            return False

        return True