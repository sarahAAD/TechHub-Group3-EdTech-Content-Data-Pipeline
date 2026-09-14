import json
import pandas as pd

from .config import CATEGORIES


def load_json_file(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"Warning: Could not find existing file at {path}")
    return []


def load_raw_data():
    all_records = []

    for category_config in CATEGORIES.values():
        records = load_json_file(category_config["output"])
        all_records.extend(records)

    return pd.DataFrame(all_records)


def profile_dataframe(df):
    profiling_metrics = []

    for column in df.columns:
        col_data = df[column]

        null_count = int(col_data.isnull().sum())

        percent_null = (
            (null_count / len(df)) * 100
            if len(df) > 0
            else 0
        )

        hashable_series = col_data.apply(
            lambda x: str(x) if isinstance(x, list) else x
        )

        unique_count = int(hashable_series.nunique())

        non_null = col_data.dropna()

        sample_val = (
            non_null.iloc[0]
            if len(non_null) > 0
            else "N/A"
        )

        profiling_metrics.append(
            {
                "column_name": column,
                "data_type": str(col_data.dtype),
                "null_count": null_count,
                "percent_null_ratio": f"{percent_null:.2f}%",
                "unique_count": unique_count,
                "sample_value_preview": str(sample_val)[:50],
            }
        )

    return pd.DataFrame(profiling_metrics)


def identify_quality_issues(df):
    issues = {}

    issues["duplicate_urls"] = (
        int(df.duplicated(subset=["url"]).sum())
        if "url" in df.columns
        else 0
    )

    issues["blank_authors"] = (
        int(
            (
                df["author"]
                .fillna("")
                .astype(str)
                .str.strip()
                == ""
            ).sum()
        )
        if "author" in df.columns
        else 0
    )

    issues["nested_tags"] = (
        df["tags"].apply(
            lambda x: isinstance(x, list)
        ).any()
        if "tags" in df.columns
        else False
    )

    return issues


def run_profiling():
    df = load_raw_data()

    profile = profile_dataframe(df)
    issues = identify_quality_issues(df)

    return df, profile, issues