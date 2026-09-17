import pandas as pd

from src.schema import (
    validate_dataframe,
    validate_row,
)


def make_valid_row(
    **overrides,
):

    row = {
        "source":
            "Medium",

        "category":
            "AI",

        "title":
            "AI Tutorial",

        "author":
            "Author",

        "publication_date":
            "2026-01-01",

        "description":
            "Tutorial",

        "url":
            "https://example.com/article",

        "content":
            "Educational content",

        "tags":
            "AI",
    }

    row.update(
        overrides
    )

    return pd.Series(
        row
    )


def test_valid_row():

    row = make_valid_row()

    reasons = validate_row(
        row
    )

    assert reasons == []


def test_empty_title_rejected():

    row = make_valid_row(
        title=""
    )

    reasons = validate_row(
        row
    )

    assert (
        "title is empty"
        in reasons
    )


def test_invalid_url_rejected():

    row = make_valid_row(
        url="not-a-url"
    )

    reasons = validate_row(
        row
    )

    assert (
        "url is missing or invalid"
        in reasons
    )


def test_invalid_date_rejected():

    row = make_valid_row(
        publication_date=
            "not-a-date"
    )

    reasons = validate_row(
        row
    )

    assert (
        "publication_date is invalid"
        in reasons
    )


def test_missing_date_allowed():

    row = make_valid_row(
        publication_date=""
    )

    reasons = validate_row(
        row
    )

    assert (
        "publication_date is invalid"
        not in reasons
    )


def test_missing_author_allowed():

    row = make_valid_row(
        author=""
    )

    reasons = validate_row(
        row
    )

    assert reasons == []


def test_missing_content_rejected():

    row = make_valid_row(
        content=""
    )

    reasons = validate_row(
        row
    )

    assert (
        "content is empty"
        in reasons
    )


def test_freecodecamp_missing_content_allowed():

    row = make_valid_row(
        source="freeCodeCamp",
        content="",
    )

    reasons = validate_row(
        row
    )

    assert (
        "content is empty"
        not in reasons
    )


def test_unsupported_source_rejected():

    row = make_valid_row(
        source="RandomWebsite"
    )

    reasons = validate_row(
        row
    )

    assert any(
        "unsupported source"
        in reason
        for reason in reasons
    )


def test_dataframe_separates_valid_and_rejected():

    valid_row = (
        make_valid_row()
        .to_dict()
    )

    invalid_row = (
        make_valid_row(
            title=""
        )
        .to_dict()
    )

    df = pd.DataFrame(
        [
            valid_row,
            invalid_row,
        ]
    )

    validated, rejected = (
        validate_dataframe(
            df
        )
    )

    assert len(validated) == 1

    assert len(rejected) == 1

    assert (
        "rejection_reason"
        in rejected.columns
    )