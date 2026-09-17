"""
Validation for the unified EdTech content schema.

Valid rows and rejected rows are kept separately so that
data-quality problems remain visible rather than silently
dropping records.
"""

from urllib.parse import urlparse

import pandas as pd

from .config import (
    COMMON_COLUMNS,
    SUPPORTED_SOURCES,
)


# ============================================================
# HELPERS
# ============================================================

def is_blank(value):
    """
    Return True for missing or empty values.
    """

    if pd.isna(value):
        return True

    return str(value).strip() == ""


def is_valid_url(value):
    """
    Validate basic HTTP/HTTPS URL structure.
    """

    if is_blank(value):
        return False

    parsed = urlparse(
        str(value).strip()
    )

    return (
        parsed.scheme
        in {"http", "https"}
        and bool(parsed.netloc)
    )


def is_valid_date_or_blank(value):
    """
    Missing dates are allowed because some sources
    such as the GeeksforGeeks dataset do not provide them.

    If a date exists, however, it must be parseable.
    """

    if is_blank(value):
        return True

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    return not pd.isna(parsed)


# ============================================================
# ROW VALIDATION
# ============================================================

def validate_row(row):
    """
    Validate one normalized article.

    Returns a list of rejection reasons.
    An empty list means the row is valid.
    """

    reasons = []

    # Required schema columns.
    for column in COMMON_COLUMNS:

        if column not in row.index:

            reasons.append(
                f"missing column: {column}"
            )

    source = str(
        row.get("source", "")
    ).strip()

    if source not in SUPPORTED_SOURCES:

        reasons.append(
            f"unsupported source: {source}"
        )

    # Title is essential.
    if is_blank(
        row.get("title")
    ):

        reasons.append(
            "title is empty"
        )

    # URL is essential.
    if not is_valid_url(
        row.get("url")
    ):

        reasons.append(
            "url is missing or invalid"
        )

    # Date can be missing, but cannot be malformed.
    if not is_valid_date_or_blank(
        row.get(
            "publication_date"
        )
    ):

        reasons.append(
            "publication_date is invalid"
        )

    # Educational article content should normally exist.
    #
    # The current freeCodeCamp scraper is temporarily
    # exempt because it currently collects article
    # metadata but not the full article body.
    if (
        source != "freeCodeCamp"
        and is_blank(
            row.get("content")
        )
    ):

        reasons.append(
            "content is empty"
        )

    return reasons


# ============================================================
# DATAFRAME VALIDATION
# ============================================================

def validate_dataframe(
    df: pd.DataFrame,
):
    """
    Validate every article.

    Returns:
        validated_df,
        rejected_df
    """

    validated_rows = []
    rejected_rows = []

    for _, row in df.iterrows():

        reasons = validate_row(
            row
        )

        record = row.to_dict()

        if reasons:

            record[
                "rejection_reason"
            ] = "; ".join(reasons)

            rejected_rows.append(
                record
            )

        else:

            validated_rows.append(
                record
            )

    validated_df = pd.DataFrame(
        validated_rows
    )

    rejected_df = pd.DataFrame(
        rejected_rows
    )

    return (
        validated_df,
        rejected_df,
    )