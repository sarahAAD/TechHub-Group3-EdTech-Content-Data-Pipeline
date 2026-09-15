"""
Task 2 — Profiling helpers.

Used by clean.py to inspect a dataframe before cleaning it.
"""

import pandas as pd


def profile_dataframe(df):
    """
    Returns a summary dataframe: one row per column with dtype, null count,
    percent null, unique count, and a sample value.
    """
    profile_rows = []
    for col in df.columns:
        profile_rows.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "null_count": df[col].isnull().sum(),
            "percent_null": round(df[col].isnull().mean() * 100, 1),
            "unique_count": df[col].nunique(),
            "sample_value": df[col].dropna().iloc[0] if df[col].notna().any() else None
        })

    return pd.DataFrame(profile_rows)


def print_data_quality_checks(df):
    """
    Prints duplicate counts, topic distribution, and placeholder-value counts
    (e.g. "No author") for a quick data quality read before cleaning.
    """
    print(f"Duplicate rows (full row): {df.duplicated().sum()}")
    print(f"Duplicate URLs: {df.duplicated(subset=['url']).sum()}")
    print(f"\nTopic distribution:\n{df['topic'].value_counts()}")
    print(f"\n'No author' count: {(df['author'] == 'No author').sum()}")
    print(f"'No date' count: {(df['publication_date'] == 'No date').sum()}")
    print(f"'No description' count: {(df['description'] == 'No description').sum()}")