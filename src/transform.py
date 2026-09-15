"""
Task 4 — Join, Transformation Rules and Testing

Applies transformation rules to the validated freeCodeCamp dataset and
saves the final analysis-ready CSV to data/processed/final.csv.

Join specification:
- Current state: single source (freeCodeCamp), so no join between two
  tables is performed at this stage.
- Planned join (once merged with teammates' sources): stack (concatenate)
  each source's validated rows, keyed on `url` (unique across sources),
  then deduplicate on `url` in case an article is cross-posted.

Transformation rules:

| Rule ID | Description                                    | Input Column(s)  | Output Column    |
|---------|-------------------------------------------------|-------------------|-------------------|
| R1      | Extract the publication year from the date       | publication_date  | publish_year      |
| R2      | Count how many keywords matched                  | matched_keywords  | keyword_count     |
| R3      | Classify article length by description length    | description       | length_category   |
"""

import pandas as pd


def count_keywords(value):
    """R2: counts comma-separated keywords in matched_keywords (0 if empty/none)."""
    if pd.isna(value) or str(value).strip().lower() == "none":
        return 0
    return len(str(value).split(","))


def classify_length(description):
    """R3: classifies an article as short/medium/long by description length."""
    if pd.isna(description):
        return "unknown"
    length = len(str(description))
    if length < 100:
        return "short"
    elif length < 200:
        return "medium"
    else:
        return "long"


def apply_transformation_rules(df):
    """
    Applies R1, R2, R3 to df and returns a new dataframe with the three
    added columns: publish_year, keyword_count, length_category.
    """
    df_final = df.copy()

    # R1
    df_final["publish_year"] = pd.to_datetime(
        df_final["publication_date"], errors="coerce"
    ).dt.year

    # R2
    df_final["keyword_count"] = df_final["matched_keywords"].apply(count_keywords)

    # R3
    df_final["length_category"] = df_final["description"].apply(classify_length)

    return df_final


def transform_freecodecamp(
    input_file="data/interim/validated.csv",
    output_file="data/processed/final.csv"
):
    """
    Runs the full Task 4 pipeline for freeCodeCamp: load validated data ->
    apply transformation rules -> save the final analysis-ready CSV.
    Returns the path to the saved file.

    Note: rule tests live in tests/test_transform.py, not here — run them
    with `pytest tests/test_transform.py`.
    """
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows")

    df_final = apply_transformation_rules(df)

    print(f"\nlength_category distribution:\n{df_final['length_category'].value_counts()}")
    print(f"\npublish_year distribution:\n{df_final['publish_year'].value_counts().sort_index()}")

    df_final.to_csv(output_file, index=False)
    print(f"\nSaved {len(df_final)} rows to {output_file}")

    return output_file


# Lets you test this file alone: `python src/transform.py` from the repo root
if __name__ == "__main__":
    transform_freecodecamp()