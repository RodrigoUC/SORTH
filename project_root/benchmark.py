import time
import random

from src.scheduling.scheduler import Scheduler
from src.scheduling.schedule_state import ScheduleState
from src.scheduling.time_model import TimeModel
from src.scheduling.classroom import Classroom
from src.scheduling.group import Group


def generate_classrooms():
    classrooms = []

    # 5 normal rooms
    for i in range(5):
        classrooms.append(Classroom(f"Room{i+1}", 30, "Normal"))

    # 3 laboratories
    for i in range(3):
        classrooms.append(Classroom(f"Lab{i+1}", 25, "Laboratory"))

    return classrooms


def generate_groups(n):
    groups = []

    for i in range(n):
        room_type = "Laboratory" if random.random() < 0.8 else "Normal"
        duration = random.choice([2, 3])

        groups.append(
            Group(
                group_id=f"G{i+1}",
                course_code=f"C{i+1}",
                duration=duration,
                required_room_type=room_type
            )
        )

    return groups


def run_test(num_groups):
    time_model = TimeModel(days=5, blocks_per_day=8)
    classrooms = generate_classrooms()
    state = ScheduleState(time_model, classrooms)

    groups = generate_groups(num_groups)

    scheduler = Scheduler()

    start = time.time()
    success = scheduler.schedule(state, groups)
    end = time.time()

    print(f"Groups: {num_groups}")
    print(f"Success: {success}")
    print(f"Time: {end - start:.4f} seconds")
    print("-" * 40)


if __name__ == "__main__":
    for n in [10, 15, 20, 25, 30]:
        run_test(n)