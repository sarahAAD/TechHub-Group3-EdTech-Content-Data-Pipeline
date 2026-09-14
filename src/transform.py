import pandas as pd

from .config import (
    VALIDATED_CSV_PATH,
    FINAL_CSV_PATH,
)


# ==============================================================================
# LOAD VALIDATED DATA
# ==============================================================================

def load_validated_data():
    """
    Load the validated dataset produced by Task 3.
    """

    if not VALIDATED_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing validated dataset: "
            f"{VALIDATED_CSV_PATH}"
        )

    df = pd.read_csv(
        VALIDATED_CSV_PATH
    )

    print(
        f"Loaded validated dataset. "
        f"Shape: {df.shape}"
    )

    return df


# ==============================================================================
# R1 - WORD COUNT
# ==============================================================================

def add_word_count(df):
    """
    R1:
    Calculate the number of words in article content.

    Input:
        content

    Output:
        word_count
    """

    df = df.copy()

    df["word_count"] = (
        df["content"]
        .fillna("")
        .astype(str)
        .str.split()
        .str.len()
    )

    return df


# ==============================================================================
# R2 - MISSING AUTHOR
# ==============================================================================

def fill_missing_author(df):
    """
    R2:
    Replace missing or empty author values with
    'Unknown'.

    Input:
        author

    Output:
        author
    """

    df = df.copy()

    df["author"] = (
        df["author"]
        .replace("", pd.NA)
        .fillna("Unknown")
    )

    return df


# ==============================================================================
# R3 - LONG FORM FLAG
# ==============================================================================

def add_long_form_flag(df):
    """
    R3:
    Identify articles containing more than 500 words.

    Input:
        word_count

    Output:
        is_long_form
    """

    df = df.copy()

    df["is_long_form"] = (
        df["word_count"] > 500
    )

    return df


# ==============================================================================
# COMPLETE TRANSFORMATION PIPELINE
# ==============================================================================

def transform_dataframe(df):
    """
    Apply all Task 4 transformation rules.
    """

    df_transformed = df.copy()

    df_transformed = add_word_count(
        df_transformed
    )

    df_transformed = fill_missing_author(
        df_transformed
    )

    df_transformed = add_long_form_flag(
        df_transformed
    )

    return df_transformed


# ==============================================================================
# SAVE FINAL DATA
# ==============================================================================

def save_final_data(df):
    """
    Save the final analysis-ready dataset.
    """

    df.to_csv(
        FINAL_CSV_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        f"Final dataset saved to: "
        f"{FINAL_CSV_PATH}"
    )


# ==============================================================================
# TASK 4 PIPELINE
# ==============================================================================

def run_transformation():
    """
    Run the complete Task 4 transformation process.
    """

    df_validated = load_validated_data()

    df_final = transform_dataframe(
        df_validated
    )

    save_final_data(
        df_final
    )

    print(
        f"Final dataset shape: "
        f"{df_final.shape}"
    )

    return df_final