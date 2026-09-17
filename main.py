"""
Run the complete unified EdTech Content Data Pipeline.

Default:
    python main.py

Uses existing raw files and extracts only missing sources.

Force re-extraction:
    python main.py --refresh
"""

import argparse

from src.clean import (
    combine_cleaned_sources,
)

from src.config import (
    CLEANED_CSV_PATH,
    FINAL_CSV_PATH,
    REJECTED_CSV_PATH,
    SUPPORTED_SOURCES,
    VALIDATED_CSV_PATH,
)

from src.extract import (
    load_all_raw,
    run_extraction,
)

from src.profile import (
    identify_quality_issues,
    profile_dataframe,
)

from src.schema import (
    validate_dataframe,
)

from src.transform import (
    select_final_columns,
    transform_dataframe,
)


def print_section(
    title,
):

    print(
        "\n"
        + "=" * 70
    )

    print(title)

    print(
        "=" * 70
    )


def run_pipeline(
    refresh=False,
):

    # ========================================================
    # TASK 1 — EXTRACT
    # ========================================================

    print_section(
        "TASK 1 — DATA EXTRACTION"
    )

    run_extraction(
        refresh=refresh
    )


    # ========================================================
    # LOAD RAW DATA
    # ========================================================

    print_section(
        "LOAD RAW DATA"
    )

    raw_datasets = (
        load_all_raw(
            SUPPORTED_SOURCES
        )
    )

    for (
        source,
        df,
    ) in (
        raw_datasets.items()
    ):

        print(
            f"{source}: "
            f"{len(df)} rows"
        )


    # ========================================================
    # TASK 2 — PROFILE
    # ========================================================

    print_section(
        "TASK 2 — DATA PROFILING"
    )

    for (
        source,
        df,
    ) in (
        raw_datasets.items()
    ):

        print(
            f"\n--- {source} ---"
        )

        profile = (
            profile_dataframe(
                df
            )
        )

        print(
            profile.to_string(
                index=False
            )
        )

        issues = (
            identify_quality_issues(
                df
            )
        )

        print(
            "\nQuality issues:"
        )

        for (
            issue,
            value,
        ) in issues.items():

            print(
                f"  {issue}: "
                f"{value}"
            )


    # ========================================================
    # TASK 2 — CLEAN + STANDARDIZE
    # ========================================================

    print_section(
        "TASK 2 — CLEAN AND STANDARDIZE"
    )

    cleaned_df = (
        combine_cleaned_sources(
            raw_datasets
        )
    )

    cleaned_df.to_csv(
        CLEANED_CSV_PATH,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Cleaned rows: "
        f"{len(cleaned_df)}"
    )

    print(
        "\nRows by source:"
    )

    print(
        cleaned_df[
            "source"
        ]
        .value_counts()
        .to_string()
    )


    # ========================================================
    # TASK 3 — VALIDATE
    # ========================================================

    print_section(
        "TASK 3 — SCHEMA VALIDATION"
    )

    (
        validated_df,
        rejected_df,
    ) = validate_dataframe(
        cleaned_df
    )

    validated_df.to_csv(
        VALIDATED_CSV_PATH,
        index=False,
        encoding="utf-8",
    )

    rejected_df.to_csv(
        REJECTED_CSV_PATH,
        index=False,
        encoding="utf-8",
    )

    total = len(
        cleaned_df
    )

    valid_count = len(
        validated_df
    )

    rejected_count = len(
        rejected_df
    )

    pass_rate = (
        valid_count
        / total
        * 100
        if total
        else 0
    )

    print(
        f"Validated: "
        f"{valid_count}"
    )

    print(
        f"Rejected: "
        f"{rejected_count}"
    )

    print(
        f"Pass rate: "
        f"{pass_rate:.2f}%"
    )

    if rejected_count:

        print(
            "\nRejection reasons:"
        )

        print(
            rejected_df[
                "rejection_reason"
            ]
            .value_counts()
            .head(20)
            .to_string()
        )


    # ========================================================
    # TASK 4 — TRANSFORM
    # ========================================================

    print_section(
        "TASK 4 — TRANSFORMATION"
    )

    transformed_df = (
        transform_dataframe(
            validated_df
        )
    )

    final_df = (
        select_final_columns(
            transformed_df
        )
    )

    final_df.to_csv(
        FINAL_CSV_PATH,
        index=False,
        encoding="utf-8",
    )

    print(
        f"Final rows: "
        f"{len(final_df)}"
    )

    print(
        "\nFinal rows by source:"
    )

    print(
        final_df[
            "source"
        ]
        .value_counts()
        .to_string()
    )

    print(
        "\nSaved:"
    )

    print(
        FINAL_CSV_PATH
    )

    print_section(
        "PIPELINE COMPLETE"
    )

    return final_df


def main():

    parser = (
        argparse.ArgumentParser(
            description=(
                "Unified EdTech "
                "content pipeline"
            )
        )
    )

    parser.add_argument(
        "--refresh",
        action="store_true",
        help=(
            "Force all sources "
            "to be extracted again."
        ),
    )

    args = (
        parser.parse_args()
    )

    run_pipeline(
        refresh=args.refresh
    )


if __name__ == "__main__":
    main()