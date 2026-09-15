"""Runs the complete dev.to ETL pipeline end to end:

Task 1 (extract) -> Task 2 (profile + clean) -> Task 3 (schema validate) -> Task 4 (transform).

Each task's logic lives in src/ (extract.py, profile.py, clean.py, schema.py, transform.py);
this file just orchestrates them in order, same as each notebook does on its own step.
"""

from src import clean, extract, profile, schema, transform


def main():
    print("=" * 73)
    print("TASK 1 -- EXTRACT")
    print("=" * 73)
    extract.run_extraction()

    print("\n" + "=" * 73)
    print("TASK 2 -- PROFILE + CLEAN")
    print("=" * 73)
    raw_records, profile_summary = profile.run_profiling()
    print(profile_summary)
    clean.run_cleaning(raw_records)

    print("\n" + "=" * 73)
    print("TASK 3 -- SCHEMA VALIDATION")
    print("=" * 73)
    schema.run_schema_validation()

    print("\n" + "=" * 73)
    print("TASK 4 -- JOIN / TRANSFORM")
    print("=" * 73)
    final_df = transform.run_transformation()

    print("\nPipeline complete.")
    return final_df


if __name__ == "__main__":
    main()
