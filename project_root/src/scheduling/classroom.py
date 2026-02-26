# src/scheduling/classroom.py

class Classroom:

    def __init__(self, name: str, capacity: int, room_type: str, time_model=None):
        self.name = name
        self.capacity = capacity
        self.room_type = room_type
        self.time_model = time_model

        # Ocupación: (day_index, block_index) -> bool
        self.occupancy = {}

    def is_available(self, day: int, start_block: int, duration: int) -> bool:
        for i in range(duration):
            key = (day, start_block + i)
            if self.occupancy.get(key, False):
                return False
        return True

    def occupy(self, day: int, start_block: int, duration: int):
        for i in range(duration):
            key = (day, start_block + i)
            self.occupancy[key] = True

    def release(self, day: int, start_block: int, duration: int):
        for i in range(duration):
            key = (day, start_block + i)
            self.occupancy[key] = False