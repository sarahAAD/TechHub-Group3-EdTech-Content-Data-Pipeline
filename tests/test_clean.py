import pandas as pd

from src.clean import (
    to_snake_case,
    flatten_tags,
    standardize_dates,
    remove_duplicates,
    clean_string_columns,
    standardize_column_names,
    clean_dataframe,
)


def test_to_snake_case():
    assert to_snake_case("PublicationDate") == "publication_date"
    assert to_snake_case("ArticleTitle") == "article_title"
    assert to_snake_case("url") == "url"


def test_flatten_tags():
    df = pd.DataFrame({
        "tags": [
            ["AI", "Python"],
            ["Cloud"],
            "",
        ]
    })

    result = flatten_tags(df)

    assert result.loc[0, "tags"] == "AI, Python"
    assert result.loc[1, "tags"] == "Cloud"
    assert result.loc[2, "tags"] == ""


def test_standardize_dates():
    df = pd.DataFrame({
        "publication_date": [
            "2026-09-14",
            "September 1, 2026",
            "invalid-date",
        ]
    })

    result = standardize_dates(df)

    assert result.loc[0, "publication_date"] == "2026-09-14"
    assert result.loc[1, "publication_date"] == "2026-09-01"
    assert pd.isna(result.loc[2, "publication_date"])


def test_remove_duplicates():
    df = pd.DataFrame({
        "url": [
            "https://example.com/a",
            "https://example.com/a",
            "https://example.com/b",
        ],
        "title": [
            "First",
            "Duplicate",
            "Second",
        ],
    })

    result = remove_duplicates(df)

    assert len(result) == 2
    assert result["url"].nunique() == 2


def test_clean_string_columns():
    df = pd.DataFrame({
        "title": ["  AI Article  "],
        "author": ["  Sarah  "],
        "tags": [" AI, Python "],
        "publication_date": ["2026-09-14"],
    })

    result = clean_string_columns(df)

    assert result.loc[0, "title"] == "AI Article"
    assert result.loc[0, "author"] == "Sarah"

    # These two columns are intentionally excluded by clean_string_columns().
    assert result.loc[0, "tags"] == " AI, Python "
    assert result.loc[0, "publication_date"] == "2026-09-14"


def test_standardize_column_names():
    df = pd.DataFrame({
        "PublicationDate": ["2026-09-14"],
        "ArticleTitle": ["Example"],
    })

    result = standardize_column_names(df)

    assert list(result.columns) == [
        "publication_date",
        "article_title",
    ]


def test_clean_dataframe():
    df = pd.DataFrame({
        "source": ["  Pluralsight  ", "  Pluralsight  "],
        "title": ["  AI Basics  ", "Duplicate"],
        "author": ["  Sarah  ", "Sarah"],
        "publication_date": [
            "September 1, 2026",
            "September 1, 2026",
        ],
        "tags": [
            ["AI", "Python"],
            ["AI", "Python"],
        ],
        "url": [
            "https://example.com/article",
            "https://example.com/article",
        ],
    })

    result = clean_dataframe(df)

    assert len(result) == 1
    assert "publication_date" in result.columns
    assert "title" in result.columns

    assert result.iloc[0]["source"] == "Pluralsight"
    assert result.iloc[0]["title"] == "AI Basics"
    assert result.iloc[0]["author"] == "Sarah"
    assert result.iloc[0]["publication_date"] == "2026-09-01"
    assert result.iloc[0]["tags"] == "AI, Python"