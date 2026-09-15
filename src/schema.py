"""
Task 3 — Define Input Schema and Validate

Validates the cleaned freeCodeCamp dataset against a defined schema.
Passing rows are kept as validated; failing rows are kept as rejected,
each with a reason.


"""

import pandas as pd


VALID_TOPICS = {"AI", "Cloud", "Data Science"}


def validate_row(row):
    """Returns a list of failure reasons for a single row (empty = valid)."""
    reasons = []

    if row["source"] != "freeCodeCamp":
        reasons.append("source is not 'freeCodeCamp'")

    if pd.isna(row["title"]) or str(row["title"]).strip() == "":
        reasons.append("title is empty")

    if pd.isna(row["url"]) or not str(row["url"]).startswith("https://"):
        reasons.append("url missing or does not start with https://")

    if pd.isna(row["publication_date"]) or str(row["publication_date"]).strip() == "":
        reasons.append("publication_date is missing/invalid")

    if row["topic"] not in VALID_TOPICS:
        topic_value = row["topic"]
        reasons.append(f"topic '{topic_value}' not in {VALID_TOPICS}")

    if pd.isna(row["author"]) or str(row["author"]).strip() == "":
        reasons.append("author is empty")

    return reasons


def validate_dataframe(df):
    """
    Validates every row in df against the schema.
    Returns (validated_df, rejected_df) — rejected_df has an extra
    rejection_reason column.
    """
    validated_rows = []
    rejected_rows = []

    for idx, row in df.iterrows():
        reasons = validate_row(row)
        if reasons:
            rejected_row = row.to_dict()
            rejected_row["rejection_reason"] = "; ".join(reasons)
            rejected_rows.append(rejected_row)
        else:
            validated_rows.append(row.to_dict())

    validated_df = pd.DataFrame(validated_rows)
    rejected_df = pd.DataFrame(rejected_rows)

    return validated_df, rejected_df


def validate_freecodecamp(
    input_file="data/interim/cleaned.csv",
    validated_output="data/interim/validated.csv",
    rejected_output="data/interim/rejected.csv"
):
    """
    Runs the full Task 3 pipeline for freeCodeCamp: load cleaned data ->
    validate -> save validated.csv and rejected.csv. Returns
    (validated_output, rejected_output, pass_rate).
    """
    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows")

    validated_df, rejected_df = validate_dataframe(df)

    print(f"Validated: {len(validated_df)} rows")
    print(f"Rejected: {len(rejected_df)} rows")

    if len(rejected_df) > 0:
        print("\nRejection reasons breakdown:")
        print(rejected_df["rejection_reason"].value_counts())
    else:
        print("No rejected rows — everything passed validation.")

    validated_df.to_csv(validated_output, index=False)
    rejected_df.to_csv(rejected_output, index=False)

    print(f"\nSaved {len(validated_df)} rows to {validated_output}")
    print(f"Saved {len(rejected_df)} rows to {rejected_output}")

    pass_rate = len(validated_df) / len(df) * 100
    print(f"\nPass rate: {pass_rate:.1f}%")

    return validated_output, rejected_output, pass_rate


# Lets you test this file alone: `python src/schema.py` from the repo root
if __name__ == "__main__":
    validate_freecodecamp()