"""Tests for Task 4's transformation rules (src/transform.py) -- moved here from the
assertion cells in notebooks/04_join_transform.ipynb, at the integration stage.
"""

import pandas as pd

from src.transform import (
    add_engagement_score,
    add_long_form_flag,
    add_word_count,
    fill_missing_topic,
    transform_dataframe,
)


def _sample_df():
    return pd.DataFrame(
        {
            "content_clean": ["one two three", " ".join(["word"] * 600), ""],
            "topic": ["ai", "", None],
            "reactions_count": [5, 0, 10],
            "comments_count": [1, 0, 2],
        }
    )


def test_add_word_count():
    df = add_word_count(_sample_df())
    assert list(df["word_count"]) == [3, 600, 0]


def test_fill_missing_topic():
    df = fill_missing_topic(_sample_df())
    assert list(df["topic"]) == ["ai", "Uncategorized", "Uncategorized"]


def test_add_long_form_flag():
    df = add_word_count(_sample_df())
    df = add_long_form_flag(df)
    assert list(df["is_long_form"]) == [False, True, False]


def test_add_engagement_score():
    df = add_engagement_score(_sample_df())
    assert list(df["engagement_score"]) == [6, 0, 12]


def test_transform_dataframe_applies_all_rules_and_fills_topic():
    df = transform_dataframe(_sample_df())
    assert {"word_count", "topic", "is_long_form", "engagement_score"}.issubset(df.columns)
    assert not (df["topic"] == "").any()
