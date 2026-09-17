import pandas as pd

from src.transform import (
    add_long_form_flag,
    add_publish_year,
    add_word_count,
    fill_missing_author,
    select_final_columns,
    transform_dataframe,
)


# ============================================================
# WORD COUNT
# ============================================================

def test_word_count():

    df = pd.DataFrame(
        {
            "content": [
                "one two three",
                "",
            ]
        }
    )

    result = add_word_count(
        df
    )

    assert (
        result[
            "word_count"
        ].tolist()
        == [3, 0]
    )


# ============================================================
# AUTHOR
# ============================================================

def test_missing_author():

    df = pd.DataFrame(
        {
            "author": [
                "",
                None,
                "Sarah",
            ]
        }
    )

    result = (
        fill_missing_author(
            df
        )
    )

    assert (
        result[
            "author"
        ].tolist()
        == [
            "Unknown",
            "Unknown",
            "Sarah",
        ]
    )


# ============================================================
# PUBLICATION YEAR
# ============================================================

def test_publish_year():

    df = pd.DataFrame(
        {
            "publication_date": [
                "2026-01-01",
                "",
            ]
        }
    )

    result = add_publish_year(
        df
    )

    assert (
        result.loc[
            0,
            "publish_year",
        ]
        == 2026
    )

    assert pd.isna(
        result.loc[
            1,
            "publish_year",
        ]
    )


# ============================================================
# LONG-FORM
# ============================================================

def test_long_form_flag():

    df = pd.DataFrame(
        {
            "word_count": [
                499,
                500,
                501,
            ]
        }
    )

    result = (
        add_long_form_flag(
            df,
            threshold=500,
        )
    )

    assert (
        result[
            "is_long_form"
        ].tolist()
        == [
            False,
            False,
            True,
        ]
    )


# ============================================================
# COMPLETE TRANSFORMATION
# ============================================================

def test_complete_transformation():

    df = pd.DataFrame(
        {
            "source":
                ["Medium"],

            "category":
                ["AI"],

            "title":
                ["AI Article"],

            "author":
                [""],

            "publication_date":
                ["2026-05-10"],

            "description":
                ["Description"],

            "url":
                ["https://example.com"],

            "content":
                ["one two three four"],

            "tags":
                ["AI"],
        }
    )

    result = (
        transform_dataframe(
            df
        )
    )

    assert (
        result.loc[
            0,
            "author",
        ]
        == "Unknown"
    )

    assert (
        result.loc[
            0,
            "word_count",
        ]
        == 4
    )

    assert (
        result.loc[
            0,
            "publish_year",
        ]
        == 2026
    )

    assert (
        result.loc[
            0,
            "is_long_form",
        ]
        == False
    )


def test_final_columns():

    df = pd.DataFrame(
        {
            "source":
                ["Medium"],

            "category":
                ["AI"],

            "title":
                ["Article"],

            "author":
                ["Author"],

            "publication_date":
                ["2026-01-01"],

            "description":
                ["Description"],

            "url":
                ["https://example.com"],

            "content":
                ["content"],

            "tags":
                ["AI"],

            "word_count":
                [1],

            "publish_year":
                [2026],

            "is_long_form":
                [False],

            # Should not be retained.
            "random_column":
                ["remove me"],
        }
    )

    result = (
        select_final_columns(
            df
        )
    )

    assert (
        "random_column"
        not in result.columns
    )

    assert (
        "word_count"
        in result.columns
    )

    assert (
        "publish_year"
        in result.columns
    )

    assert (
        "is_long_form"
        in result.columns
    )