import re

import pandas as pd

from .config import (
    CLEANED_CSV_PATH,
)


# ==============================================================================
# COLUMN NAME STANDARDIZATION
# ==============================================================================

def to_snake_case(name):
    """
    Convert column names to snake_case.
    """

    s1 = re.sub(
        "(.)([A-Z][a-z]+)",
        r"\1_\2",
        str(name)
    )

    return re.sub(
        "([a-z0-9])([A-Z])",
        r"\1_\2",
        s1
    ).lower().strip()


# ==============================================================================
# FLATTEN NESTED FIELDS
# ==============================================================================

def flatten_tags(df):
    """
    Convert list-based tags into comma-separated strings.
    """

    df = df.copy()

    if "tags" in df.columns:

        df["tags"] = df["tags"].apply(
            lambda x:
            ", ".join(x)
            if isinstance(x, list)
            else str(x)
        )

    return df


# ==============================================================================
# STANDARDIZE PUBLICATION DATES
# ==============================================================================

def standardize_dates(df):
    """
    Convert publication_date to YYYY-MM-DD.

    Invalid dates become NaT.
    """

    df = df.copy()

    if "publication_date" in df.columns:

        df["publication_date"] = pd.to_datetime(
            df["publication_date"],
            errors="coerce"
        ).dt.strftime(
            "%Y-%m-%d"
        )

    return df


# ==============================================================================
# REMOVE DUPLICATES
# ==============================================================================

def remove_duplicates(df):
    """
    Remove duplicate articles using URL as
    the unique identifier.
    """

    df = df.copy()

    if "url" in df.columns:

        df = df.drop_duplicates(
            subset=["url"]
        )

    return df


# ==============================================================================
# CLEAN STRING WHITESPACE
# ==============================================================================

def clean_string_columns(df):
    """
    Remove leading and trailing whitespace
    from object/string columns.
    """

    df = df.copy()

    for column in df.select_dtypes(
        include=["object"]
    ).columns:

        if column not in [
            "tags",
            "publication_date"
        ]:

            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
            )

    return df


# ==============================================================================
# STANDARDIZE COLUMN NAMES
# ==============================================================================

def standardize_column_names(df):
    """
    Convert all column names to snake_case.
    """

    df = df.copy()

    df.columns = [
        to_snake_case(column)
        for column in df.columns
    ]

    return df


# ==============================================================================
# COMPLETE CLEANING PIPELINE
# ==============================================================================

def clean_dataframe(df):
    """
    Execute all Task 2 cleaning and standardization
    operations in the same order as the notebook.
    """

    df_clean = df.copy()

    # 1. Flatten nested tags
    df_clean = flatten_tags(
        df_clean
    )

    # 2. Standardize publication dates
    df_clean = standardize_dates(
        df_clean
    )

    # 3. Remove duplicate URLs
    df_clean = remove_duplicates(
        df_clean
    )

    # 4. Clean string whitespace
    df_clean = clean_string_columns(
        df_clean
    )

    # 5. Standardize column names
    df_clean = standardize_column_names(
        df_clean
    )

    print(
        "Data mutation transformations finished. "
        f"Working tracking shape is down to: "
        f"{df_clean.shape} uniform rows."
    )

    return df_clean


# ==============================================================================
# SAVE CLEANED DATA
# ==============================================================================

def save_cleaned_data(df):
    """
    Save the cleaned DataFrame to data/interim/cleaned.csv.
    """

    df.to_csv(
        CLEANED_CSV_PATH,
        index=False,
        encoding="utf-8"
    )

    print(
        "File flushed smoothly into relative "
        "environment storage destination path: "
        f"{CLEANED_CSV_PATH}"
    )


# ==============================================================================
# VERIFY OUTPUT
# ==============================================================================

def verify_cleaned_data():
    """
    Read the generated CSV again and verify
    that it can be loaded successfully.
    """

    df_verification = pd.read_csv(
        CLEANED_CSV_PATH
    )

    print(
        "========================================================================="
    )

    print(
        "INTERIM CHECKPOINT DISK VALIDATION DETAILS"
    )

    print(
        "========================================================================="
    )

    print(
        f"CSV Rows Read: "
        f"{df_verification.shape[0]}"
    )

    print(
        f"CSV Column Names: "
        f"{list(df_verification.columns)}"
    )

    if not df_verification.empty:

        print(
            "\nFirst row sneak-preview "
            "column properties:"
        )

        print(
            df_verification.iloc[0].to_dict()
        )

    return df_verification


# ==============================================================================
# TASK 2 CLEANING PIPELINE
# ==============================================================================

def run_cleaning(df):
    """
    Run the complete Task 2 cleaning process,
    save the result, and verify the output.
    """

    df_clean = clean_dataframe(
        df
    )

    save_cleaned_data(
        df_clean
    )

    df_verification = (
        verify_cleaned_data()
    )

    return (
        df_clean,
        df_verification
    )