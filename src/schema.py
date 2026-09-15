"""Task 3 -- define the input schema and validate the cleaned dataset against it.

Moved here, unchanged in behaviour, from notebooks/03_schema_validate.ipynb.
"""

import pandas as pd
from jsonschema import Draft7Validator

from .config import CLEANED_CSV_PATH, REJECTED_CSV_PATH, VALIDATED_CSV_PATH


# ==============================================================================
# SCHEMA DEFINITION
#
# | Column                 | Data Type              | Nullable | Allowed Values / Range          |
# |-------------------------|------------------------|----------|----------------------------------|
# | external_id             | string                 | N        | must match `devto:<digits>`     |
# | title                   | string                 | N        | non-empty                       |
# | source                  | string                 | N        | must equal `dev.to`             |
# | author                  | string                 | N        | non-empty                       |
# | published_date          | string (ISO datetime)  | N        | valid ISO 8601 timestamp        |
# | url                     | string                 | N        | must start with `https://`      |
# | topic                   | string                 | Y        | any string, empty allowed       |
# | tags                    | string                 | Y        | comma-separated tags, empty ok  |
# | description             | string                 | Y        | free text, empty allowed        |
# | content_type            | string                 | N        | must equal `article`            |
# | reading_time_minutes    | integer                | N        | >= 0                             |
# | reactions_count         | integer                | N        | >= 0                             |
# | comments_count          | integer                | N        | >= 0                             |
# | cover_image             | string (URL)           | Y        | starts with `http` when present |
# | content_markdown        | string                 | Y        | empty allowed if fetch failed   |
# | content_html            | string                 | Y        | empty allowed if fetch failed   |
# | content_clean           | string                 | Y        | empty allowed if fetch failed   |
# ==============================================================================

SCHEMA = {
    "type": "object",
    "required": [
        "external_id", "title", "source", "author", "published_date", "url",
        "content_type", "reading_time_minutes", "reactions_count", "comments_count",
    ],
    "properties": {
        "external_id": {"type": "string", "pattern": r"^devto:\d+$"},
        "title": {"type": "string", "minLength": 1},
        "source": {"type": "string", "enum": ["dev.to"]},
        "author": {"type": "string", "minLength": 1},
        "published_date": {"type": "string", "minLength": 1},
        "url": {"type": "string", "pattern": r"^https://"},
        "topic": {"type": ["string", "null"]},
        "tags": {"type": ["string", "null"]},
        "description": {"type": ["string", "null"]},
        "content_type": {"type": "string", "enum": ["article"]},
        "reading_time_minutes": {"type": "number", "minimum": 0},
        "reactions_count": {"type": "number", "minimum": 0},
        "comments_count": {"type": "number", "minimum": 0},
        "cover_image": {"type": ["string", "null"]},
        "content_markdown": {"type": ["string", "null"]},
        "content_html": {"type": ["string", "null"]},
        "content_clean": {"type": ["string", "null"]},
    },
}


def load_cleaned_data(path=CLEANED_CSV_PATH):
    """Loads the cleaned interim dataset (Task 2's output)."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required interim file: {path}")

    df = pd.read_csv(path)
    print(f"Loaded cleaned dataset. Shape: {df.shape}")
    return df


def validate_dataframe(df):
    """Validates each row against SCHEMA, routing it to validated or rejected (with reason)."""
    validator = Draft7Validator(SCHEMA)

    # JSON Schema validation needs real dicts, not a DataFrame -- NaN -> None.
    records = df.where(pd.notnull(df), None).to_dict(orient="records")

    validated_rows = []
    rejected_rows = []

    for record in records:
        errors = sorted(validator.iter_errors(record), key=lambda e: e.path)
        if not errors:
            validated_rows.append(record)
        else:
            reason = "; ".join(f"{'.'.join(map(str, e.path)) or '(row)'}: {e.message}" for e in errors)
            rejected_record = dict(record)
            rejected_record["rejection_reason"] = reason
            rejected_rows.append(rejected_record)

    df_validated = pd.DataFrame(validated_rows)
    df_rejected = pd.DataFrame(rejected_rows)
    return df_validated, df_rejected


def save_validation_results(df_validated, df_rejected, validated_path=VALIDATED_CSV_PATH, rejected_path=REJECTED_CSV_PATH):
    """Saves validated and rejected records."""
    df_validated.to_csv(validated_path, index=False)
    df_rejected.to_csv(rejected_path, index=False)

    print(f"Saved -> {validated_path} ({len(df_validated)} rows)")
    print(f"Saved -> {rejected_path} ({len(df_rejected)} rows)")


def run_schema_validation():
    """Runs the complete Task 3 schema validation process."""
    df = load_cleaned_data()
    df_validated, df_rejected = validate_dataframe(df)

    print(f"Validated: {len(df_validated)} rows")
    print(f"Rejected:  {len(df_rejected)} rows")

    save_validation_results(df_validated, df_rejected)
    return df_validated, df_rejected
