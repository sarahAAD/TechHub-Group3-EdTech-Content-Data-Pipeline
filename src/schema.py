import pandas as pd

from .config import (
    CLEANED_CSV_PATH,
    VALIDATED_CSV_PATH,
    REJECTED_CSV_PATH,
)


# ==============================================================================
# DATA INGESTION
# ==============================================================================

def load_cleaned_data():
    """Load the cleaned interim dataset."""

    if not CLEANED_CSV_PATH.exists():
        raise FileNotFoundError(
            f"Missing required interim file: {CLEANED_CSV_PATH}"
        )

    df = pd.read_csv(CLEANED_CSV_PATH)

    print(
        f"Loaded cleaned dataset successfully. "
        f"Shape: {df.shape}"
    )

    return df


# ==============================================================================
# SCHEMA DEFINITION
# ==============================================================================

SCHEMA = {
    "source": {
        "data_type": "string",
        "nullable": False,
        "allowed_values": ["Pluralsight"],
    },
    "category": {
        "data_type": "string",
        "nullable": False,
        "allowed_values": ["AI & Data", "Cloud"],
    },
    "title": {
        "data_type": "string",
        "nullable": False,
        "constraint": "non-empty",
    },
    "author": {
        "data_type": "string",
        "nullable": True,
    },
    "publication_date": {
        "data_type": "string",
        "nullable": True,
        "constraint": "YYYY-MM-DD",
    },
    "description": {
        "data_type": "string",
        "nullable": True,
    },
    "tags": {
        "data_type": "string",
        "nullable": True,
        "constraint": "comma-separated keywords",
    },
    "url": {
        "data_type": "string",
        "nullable": False,
        "constraint": "starts with https://",
    },
    "content": {
        "data_type": "string",
        "nullable": False,
        "constraint": "non-empty",
    },
    "scraped_at": {
        "data_type": "string",
        "nullable": False,
        "constraint": "valid ISO timestamp",
    },
}


# ==============================================================================
# VALIDATION
# ==============================================================================

def validate_dataframe(df):
    """
    Validate each row against the predefined input schema.

    Returns:
        df_validated: Rows that pass validation.
        df_rejected: Rows that fail validation with rejection reasons.
    """

    valid_rows = []
    rejected_rows = []

    for _, row in df.iterrows():

        row_dict = row.to_dict()

        is_valid = True
        failure_reasons = []

        # ----------------------------------------------------------------------
        # 1. Validate source
        # ----------------------------------------------------------------------

        source_raw = row_dict.get("source")

        if pd.isna(source_raw):
            source_val = ""
        else:
            source_val = str(source_raw).strip()

        if source_val != "Pluralsight":
            is_valid = False
            failure_reasons.append(
                f"Invalid source property value: '{source_val}'"
            )

        # ----------------------------------------------------------------------
        # 2. Validate category
        # ----------------------------------------------------------------------

        category_raw = row_dict.get("category")

        if pd.isna(category_raw):
            category_val = ""
        else:
            category_val = str(category_raw).strip()

        if category_val not in ["AI & Data", "Cloud"]:
            is_valid = False
            failure_reasons.append(
                f"Category value is not allowed: '{category_val}'"
            )

        # ----------------------------------------------------------------------
        # 3. Validate title
        # ----------------------------------------------------------------------

        title_raw = row_dict.get("title")

        if pd.isna(title_raw):
            title_val = ""
        else:
            title_val = str(title_raw).strip()

        if title_val == "":
            is_valid = False
            failure_reasons.append(
                "Title is blank or missing"
            )

        # ----------------------------------------------------------------------
        # 4. Validate publication_date
        #
        # Nullable = Yes
        # If a value exists, it must follow YYYY-MM-DD.
        # ----------------------------------------------------------------------

        publication_date_raw = row_dict.get("publication_date")

        if pd.isna(publication_date_raw) or str(publication_date_raw).strip() == "":
            publication_date_val = None

        else:
            publication_date_val = str(publication_date_raw).strip()

            parsed_date = pd.to_datetime(
                publication_date_val,
                format="%Y-%m-%d",
                errors="coerce"
            )

            if pd.isna(parsed_date):
                is_valid = False
                failure_reasons.append(
                    f"Publication date must follow YYYY-MM-DD format: "
                    f"'{publication_date_val}'"
                )

        # ----------------------------------------------------------------------
        # 5. Validate URL
        # ----------------------------------------------------------------------

        url_raw = row_dict.get("url")

        if pd.isna(url_raw):
            url_val = ""
        else:
            url_val = str(url_raw).strip()

        if not url_val.startswith("https://"):
            is_valid = False
            failure_reasons.append(
                "URL must start with 'https://'"
            )

        # ----------------------------------------------------------------------
        # 6. Validate content
        # ----------------------------------------------------------------------

        content_raw = row_dict.get("content")

        if pd.isna(content_raw):
            content_val = ""
        else:
            content_val = str(content_raw).strip()

        if content_val == "":
            is_valid = False
            failure_reasons.append(
                "Article content is blank or missing"
            )

        # ----------------------------------------------------------------------
        # 7. Validate scraped_at
        #
        # Nullable = No
        # Must contain a valid ISO timestamp.
        # ----------------------------------------------------------------------

        scraped_at_raw = row_dict.get("scraped_at")

        if pd.isna(scraped_at_raw):
            scraped_at_val = ""
        else:
            scraped_at_val = str(scraped_at_raw).strip()

        if scraped_at_val == "":
            is_valid = False
            failure_reasons.append(
                "Scraped timestamp is blank or missing"
            )

        else:
            parsed_timestamp = pd.to_datetime(
                scraped_at_val,
                errors="coerce"
            )

            if pd.isna(parsed_timestamp):
                is_valid = False
                failure_reasons.append(
                    f"Scraped timestamp is not a valid ISO timestamp: "
                    f"'{scraped_at_val}'"
                )

        # ----------------------------------------------------------------------
        # Route row
        # ----------------------------------------------------------------------

        if is_valid:
            valid_rows.append(row_dict)

        else:
            row_dict["rejection_reason"] = "; ".join(
                failure_reasons
            )

            rejected_rows.append(row_dict)

    df_validated = pd.DataFrame(valid_rows)
    df_rejected = pd.DataFrame(rejected_rows)

    return df_validated, df_rejected


# ==============================================================================
# OUTPUT
# ==============================================================================

def save_validation_results(
    df_input,
    df_validated,
    df_rejected
):
    """Save validated and rejected records."""

    # --------------------------------------------------------------------------
    # Validated output
    # --------------------------------------------------------------------------

    if not df_validated.empty:

        df_validated.to_csv(
            VALIDATED_CSV_PATH,
            index=False,
            encoding="utf-8"
        )

    else:

        pd.DataFrame(
            columns=df_input.columns
        ).to_csv(
            VALIDATED_CSV_PATH,
            index=False,
            encoding="utf-8"
        )

    # --------------------------------------------------------------------------
    # Rejected output
    # --------------------------------------------------------------------------

    if not df_rejected.empty:

        df_rejected.to_csv(
            REJECTED_CSV_PATH,
            index=False,
            encoding="utf-8"
        )

    else:

        pd.DataFrame(
            columns=list(df_input.columns) + ["rejection_reason"]
        ).to_csv(
            REJECTED_CSV_PATH,
            index=False,
            encoding="utf-8"
        )

    print("Validation output files saved:")
    print(f" - Validated: {VALIDATED_CSV_PATH}")
    print(f" - Rejected:  {REJECTED_CSV_PATH}")


# ==============================================================================
# MAIN TASK 3 FUNCTION
# ==============================================================================

def run_schema_validation():
    """Run the complete Task 3 schema validation process."""

    df_interim = load_cleaned_data()

    df_validated, df_rejected = validate_dataframe(
        df_interim
    )

    print("=" * 73)
    print("SCHEMA VALIDATION COMPLETE")
    print("=" * 73)

    print(
        f"Total Rows Passing Schema Validation: "
        f"{len(df_validated)}"
    )

    print(
        f"Total Rows Routed to Rejection Bucket: "
        f"{len(df_rejected)}"
    )

    save_validation_results(
        df_interim,
        df_validated,
        df_rejected
    )

    return df_validated, df_rejected