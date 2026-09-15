"""Task 2 (part 1) -- load the latest raw extract and profile it.

Moved here, unchanged in behaviour, from notebooks/02_profile_clean.ipynb.
"""

import glob
import json

import pandas as pd

from .config import RAW_DIR


def load_latest_raw():
    """Loads the most recent data/raw/devto_*.json produced by Task 1."""
    raw_files = sorted(glob.glob(str(RAW_DIR / "devto_*.json")))
    if not raw_files:
        raise FileNotFoundError(
            "No data/raw/devto_*.json found -- run the extraction step (Task 1) first."
        )

    raw_path = raw_files[-1]  # most recent
    with open(raw_path, encoding="utf-8") as f:
        raw_records = json.load(f)

    print(f"Loaded {len(raw_records)} raw records from {raw_path}")
    return raw_records, raw_path


def _hashable(v):
    """List/dict-valued columns (e.g. tag_list) aren't hashable for a naive .nunique() --
    hash them through json.dumps() instead of dropping or stringifying the column outright.
    """
    if isinstance(v, (list, dict)):
        return json.dumps(v, sort_keys=True, default=str)
    return v


def profile_dataframe(raw_df):
    """One row per column: dtype, null count, unique count, sample value."""
    profile_rows = []
    for col in raw_df.columns:
        col_series = raw_df[col]
        non_null = col_series.dropna()
        unique_count = len({_hashable(v) for v in non_null})
        profile_rows.append(
            {
                "column": col,
                "dtype": str(col_series.dtype),
                "null_count": int(col_series.isna().sum()),
                "percent_null": round(100 * col_series.isna().mean(), 1) if len(col_series) else 0.0,
                "unique_count": unique_count,
                "sample_value": non_null.iloc[0] if len(non_null) else None,
            }
        )
    return pd.DataFrame(profile_rows)


# Data-quality issues identified during profiling (full write-up in
# notebooks/02_profile_clean.ipynb) -- each one is handled explicitly in clean.py.
KNOWN_ISSUES = [
    "Nested fields: 'user' (dict) and 'tag_list' (list) come back nested from the API.",
    "Duplicate articles: the same article can appear once per tag it was fetched under.",
    "HTML / Liquid markup noise in body_markdown.",
    "Missing cover_image / organization for many articles (legitimately absent).",
    "Mixed / inconsistent date fields (published_at vs published_timestamp).",
    "A few articles may be missing body content if the per-article content fetch failed.",
    "List/dict-valued columns break naive nunique() -- handled via json.dumps() hashing.",
]


def run_profiling():
    """Runs the complete Task 2 profiling step and returns (raw_records, profile_summary)."""
    raw_records, _ = load_latest_raw()
    raw_df = pd.json_normalize(raw_records)
    profile_summary = profile_dataframe(raw_df)

    print("Shape (rows, columns):", raw_df.shape)
    print(f"{len(KNOWN_ISSUES)} known data-quality issues documented (see KNOWN_ISSUES).")

    return raw_records, profile_summary
