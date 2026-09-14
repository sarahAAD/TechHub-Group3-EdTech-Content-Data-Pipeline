import pandas as pd

from src.transform import (
    add_word_count,
    fill_missing_author,
    add_long_form_flag,
    transform_dataframe,
)


def test_word_count():
    df = pd.DataFrame({
        "content": [
            "Python is easy to learn",
            "",
            None,
        ]
    })

    result = add_word_count(df)

    assert result.loc[0, "word_count"] == 5
    assert result.loc[1, "word_count"] == 0
    assert result.loc[2, "word_count"] == 0


def test_missing_author():
    df = pd.DataFrame({
        "author": [
            "Sarah",
            "",
            None,
        ]
    })

    result = fill_missing_author(df)

    assert result.loc[0, "author"] == "Sarah"
    assert result.loc[1, "author"] == "Unknown"
    assert result.loc[2, "author"] == "Unknown"


def test_long_form():
    df = pd.DataFrame({
        "word_count": [
            499,
            500,
            501,
        ]
    })

    result = add_long_form_flag(df)

    assert result.loc[0, "is_long_form"] == False
    assert result.loc[1, "is_long_form"] == False
    assert result.loc[2, "is_long_form"] == True


def test_transform_dataframe():
    df = pd.DataFrame({
        "content": [
            "one two three",
            " ".join(["word"] * 501),
        ],
        "author": [
            "",
            "John",
        ],
    })

    result = transform_dataframe(df)

    assert result.loc[0, "word_count"] == 3
    assert result.loc[0, "author"] == "Unknown"
    assert result.loc[0, "is_long_form"] == False

    assert result.loc[1, "word_count"] == 501
    assert result.loc[1, "author"] == "John"
    assert result.loc[1, "is_long_form"] == True


def test_empty_dataframe():
    df = pd.DataFrame(
        columns=["content", "author"]
    )

    result = transform_dataframe(df)

    assert result.empty
    assert "word_count" in result.columns
    assert "is_long_form" in result.columns
