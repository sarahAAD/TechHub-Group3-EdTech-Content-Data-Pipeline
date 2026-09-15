"""Entry point for the full ETL pipeline.

Placeholder only. At the integration stage this will chain together the
functions refactored into src/ (extract -> profile/clean -> schema validate
-> join/transform) so the whole pipeline can be run end-to-end starting from
an empty data/ folder.
"""


"""Entry point for the full freeCodeCamp ETL pipeline."""

from src.extract import scrape_freecodecamp
from src.clean import profile_and_clean_freecodecamp
from src.schema import validate_freecodecamp
from src.transform import transform_freecodecamp


def main() -> None:
    print("Starting freeCodeCamp ETL pipeline...\n")

    # Task 1 - Extract
    print("=== Task 1: Extract ===")
    raw_file = scrape_freecodecamp()
    print(f"Raw data saved to: {raw_file}\n")

    # Task 2 - Profile and Clean
    print("=== Task 2: Profile and Clean ===")
    cleaned_file = profile_and_clean_freecodecamp()
    print(f"Cleaned data saved to: {cleaned_file}\n")

    # Task 3 - Schema Validation
    print("=== Task 3: Validate ===")
    validated_file, rejected_file, pass_rate = validate_freecodecamp()
    print(f"Validated data saved to: {validated_file}")
    print(f"Rejected data saved to: {rejected_file}")
    print(f"Validation pass rate: {pass_rate:.1f}%\n")

    # Task 4 - Transform
    print("=== Task 4: Transform ===")
    final_file = transform_freecodecamp()
    print(f"Final data saved to: {final_file}\n")

    print("ETL pipeline completed successfully.")


if __name__ == "__main__":
    main()