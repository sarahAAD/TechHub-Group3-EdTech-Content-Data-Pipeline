from src.extract import run_extraction
from src.profile import run_profiling
from src.clean import run_cleaning
from src.schema import run_schema_validation
from src.transform import run_transformation


def main():
    run_extraction()

    df, profile, issues = run_profiling()

    run_cleaning(df)

    run_schema_validation()

    final_df = run_transformation()

    print(f"Final rows: {len(final_df)}")
    print("Pipeline completed successfully.")


if __name__ == "__main__":
    main()