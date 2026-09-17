"""
Shared transformations for the validated EdTech dataset.

These transformations are intentionally source-independent so
that they can be applied consistently across all five sources.
"""

import pandas as pd

from .config import (
    COMMON_COLUMNS,
    LONG_FORM_WORD_THRESHOLD,
)


# ============================================================
# AUTHOR
# ============================================================

def fill_missing_author(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert missing authors to 'Unknown' after validation.

    We do this during transformation rather than ingestion so
    the raw missingness remains visible during profiling.
    """

    df = df.copy()

    df["author"] = (
        df["author"]
        .replace("", pd.NA)
        .fillna("Unknown")
    )

    return df


# ============================================================
# WORD COUNT
# ============================================================

def add_word_count(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Count words in article content.
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


# ============================================================
# PUBLICATION YEAR
# ============================================================

def add_publish_year(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract publication year when a date is available.
    """

    df = df.copy()

    df["publish_year"] = (
        pd.to_datetime(
            df["publication_date"],
            errors="coerce",
        )
        .dt.year
    )

    return df


# ============================================================
# LONG-FORM FLAG
# ============================================================

def add_long_form_flag(
    df: pd.DataFrame,
    threshold=LONG_FORM_WORD_THRESHOLD,
) -> pd.DataFrame:
    """
    Flag articles containing more than the configured
    number of words.
    """

    df = df.copy()

    df["is_long_form"] = (
        df["word_count"]
        > threshold
    )

    return df


# ============================================================
# COMPLETE TRANSFORMATION
# ============================================================

def transform_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Apply all shared transformation rules.
    """

    transformed = df.copy()

    transformed = (
        fill_missing_author(
            transformed
        )
    )

    transformed = (
        add_word_count(
            transformed
        )
    )

    transformed = (
        add_publish_year(
            transformed
        )
    )

    transformed = (
        add_long_form_flag(
            transformed
        )
    )

    return transformed


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

def select_final_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce the final analysis-ready column order.
    """

    derived_columns = [
        "word_count",
        "publish_year",
        "is_long_form",
    ]

    final_columns = (
        COMMON_COLUMNS
        + derived_columns
    )

    available_columns = [
        column
        for column in final_columns
        if column in df.columns
    ]

    return df[
        available_columns
    ].copy()