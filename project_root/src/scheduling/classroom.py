class Classroom:

    def __init__(self, name: str, capacity: int, room_type: str):
        self.name = name
        self.capacity = capacity
        self.room_type = room_type

        # {(day, block): True}
        self.occupied_slots = {}

    def is_available(self, day: int, start_block: int, duration: int) -> bool:
        for block in range(start_block, start_block + duration):
            if (day, block) in self.occupied_slots:
                return False
        return True

    def occupy(self, day: int, start_block: int, duration: int) -> None:
        for block in range(start_block, start_block + duration):
            self.occupied_slots[(day, block)] = True

    def release(self, day: int, start_block: int, duration: int) -> None:
        for block in range(start_block, start_block + duration):
            self.occupied_slots.pop((day, block), None)