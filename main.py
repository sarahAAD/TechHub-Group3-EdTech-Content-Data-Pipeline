from src.profile import run_profiling
from src.clean import run_cleaning
from src.schema import run_schema_validation


def main():
    # Task 2
    run_profiling()
    run_cleaning()

    # Task 3
    run_schema_validation()


if __name__ == "__main__":
    main()