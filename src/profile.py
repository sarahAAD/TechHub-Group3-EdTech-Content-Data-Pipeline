"""
Reusable data profiling utilities.

These functions work with any of the five source datasets.
"""

import pandas as pd


# ============================================================
# COLUMN PROFILING
# ============================================================

def profile_dataframe(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce basic profiling statistics for every column.

    Metrics:
    - data type
    - null count
    - null percentage
    - unique count
    - example value
    """

    profiling_metrics = []

    for column in df.columns:

        series = df[column]

        null_count = int(
            series.isna().sum()
        )

        if len(df) > 0:
            percent_null = (
                null_count / len(df)
            ) * 100
        else:
            percent_null = 0.0

        # Lists/dicts cannot always be counted directly.
        hashable_series = series.apply(
            lambda value:
                str(value)
                if isinstance(value, (list, dict))
                else value
        )

        unique_count = int(
            hashable_series.nunique(
                dropna=True
            )
        )

        non_null = series.dropna()

        if len(non_null) > 0:
            sample_value = str(
                non_null.iloc[0]
            )[:100]
        else:
            sample_value = "N/A"

        profiling_metrics.append(
            {
                "column_name": column,
                "data_type": str(series.dtype),
                "null_count": null_count,
                "percent_null": round(
                    percent_null,
                    2,
                ),
                "unique_count": unique_count,
                "sample_value": sample_value,
            }
        )

    return pd.DataFrame(
        profiling_metrics
    )


# ============================================================
# QUALITY CHECKS
# ============================================================

def identify_quality_issues(
    df: pd.DataFrame,
) -> dict:
    """
    Identify common quality problems without modifying the data.
    """

    issues = {}

    if "url" in df.columns:
        issues["duplicate_urls"] = int(
            df["url"]
            .duplicated()
            .sum()
        )

    for column in [
        "title",
        "author",
        "content",
    ]:

        if column in df.columns:

            blank_count = (
                df[column]
                .fillna("")
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            issues[
                f"blank_{column}"
            ] = int(blank_count)

    return issues