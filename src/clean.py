"""
Task 2 — Data Discovery, Profiling and Cleaning

Loads the freeCodeCamp dataset produced by extract.py, profiles it,
cleans it, and saves the result to data/interim/cleaned.csv.
"""

import pandas as pd
import glob

from src.profile import profile_dataframe, print_data_quality_checks


def load_latest_raw(pattern="data/raw/freecodecamp_*.csv"):
    """Loads whichever freecodecamp_*.csv is newest in data/raw/."""
    raw_files = glob.glob(pattern)
    latest_file = sorted(raw_files)[-1]
    print(f"Loading: {latest_file}")

    df = pd.read_csv(latest_file)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    return df


def clean_freecodecamp(df):
    """
    Cleans the freeCodeCamp dataframe:
    - drops exact duplicate rows and duplicate URLs
    - standardises publication_date into a plain date, keeping the full
      timestamp in a separate column
    - fills the matched_keywords enrichment column with "none" instead of
      leaving it NaN
    """
    df_clean = df.copy()

    df_clean = df_clean.drop_duplicates()
    df_clean = df_clean.drop_duplicates(subset=["url"])

    df_clean["publication_datetime"] = pd.to_datetime(
        df_clean["publication_date"], errors="coerce", utc=True
    )
    df_clean["publication_date"] = df_clean["publication_datetime"].dt.date

    df_clean["matched_keywords"] = df_clean["matched_keywords"].fillna("none")

    # Column names are already snake_case, nothing to rename here

    return df_clean


def profile_and_clean_freecodecamp(
    raw_glob_pattern="data/raw/freecodecamp_*.csv",
    output_file="data/interim/cleaned.csv"
):
    """
    Runs the full Task 2 pipeline for freeCodeCamp: load -> profile -> clean
    -> save. Returns the path to the saved cleaned CSV.
    """
    df = load_latest_raw(raw_glob_pattern)

    profile_df = profile_dataframe(df)
    print("\nColumn profile:")
    print(profile_df)

    print_data_quality_checks(df)

    df_clean = clean_freecodecamp(df)
    print(f"\nRows before cleaning: {len(df)}")
    print(f"Rows after cleaning: {len(df_clean)}")

    df_clean.to_csv(output_file, index=False)
    print(f"Saved {len(df_clean)} rows to {output_file}")

    return output_file


# Lets you test this file alone: `python src/clean.py` from the repo root
if __name__ == "__main__":
    profile_and_clean_freecodecamp()