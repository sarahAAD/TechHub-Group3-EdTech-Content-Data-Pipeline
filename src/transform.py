"""Task 4 -- transformation rules applied to the validated dev.to dataset.

Moved here, unchanged in behaviour, from notebooks/04_join_transform.ipynb.

Note on "join": for this source, the join across raw listings (by tag) already happens
in extract.py, and duplicates are dropped by url in clean.py. Joining *across* group
members' sources (dev.to + the other sources) happens later, at the project-wide
integration stage, once everyone's final.csv is ready.
"""

import pandas as pd

from .config import FINAL_CSV_PATH, LONG_FORM_WORD_THRESHOLD, VALIDATED_CSV_PATH


def load_validated_data(path=VALIDATED_CSV_PATH):
    """Loads the validated dataset produced by Task 3."""
    if not path.exists():
        raise FileNotFoundError(f"Missing validated dataset: {path}")

    df = pd.read_csv(path)
    print(f"Loaded validated data. Shape: {df.shape}")
    return df


def add_word_count(df):
    """R1: word count of the cleaned, plain-text article body."""
    df = df.copy()
    df["word_count"] = df["content_clean"].fillna("").astype(str).apply(lambda x: len(x.split()))
    return df


def fill_missing_topic(df):
    """R2: replace missing/blank topic values with 'Uncategorized'."""
    df = df.copy()
    df["topic"] = (
        df["topic"]
        .astype(str)
        .str.strip()
        .replace({"": "Uncategorized", "nan": "Uncategorized", "None": "Uncategorized"})
    )
    return df


def add_long_form_flag(df, threshold=LONG_FORM_WORD_THRESHOLD):
    """R3: True when word_count > threshold (500 -- same threshold used for the
    Pluralsight source, so the two datasets line up when combined at integration).
    """
    df = df.copy()
    df["is_long_form"] = df["word_count"] > threshold
    return df


def add_engagement_score(df):
    """R4: dev.to-specific engagement metric -- reactions + comments."""
    df = df.copy()
    df["engagement_score"] = df["reactions_count"].fillna(0) + df["comments_count"].fillna(0)
    return df


def transform_dataframe(df):
    """Applies all Task 4 transformation rules, in order."""
    df_transformed = df.copy()
    df_transformed = add_word_count(df_transformed)
    df_transformed = fill_missing_topic(df_transformed)
    df_transformed = add_long_form_flag(df_transformed)
    df_transformed = add_engagement_score(df_transformed)
    return df_transformed


def save_final_data(df, path=FINAL_CSV_PATH):
    """Saves the final, analysis-ready dataset."""
    df.to_csv(path, index=False)
    print(f"Final dataset saved to: {path}")


def run_transformation():
    """Runs the complete Task 4 transformation process."""
    df_validated = load_validated_data()
    df_final = transform_dataframe(df_validated)
    save_final_data(df_final)
    print(f"Final dataset shape: {df_final.shape}")
    return df_final
