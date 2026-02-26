from src.application.scheduling_service import SchedulingService


def main():
    service = SchedulingService("data/input/horarios.xlsx")
    assignments = service.run()

    for a in assignments:
        print(a)


if __name__ == "__main__":
    main()