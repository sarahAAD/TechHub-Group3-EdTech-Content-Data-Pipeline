"""Placeholder. Populated at the integration stage by moving the assertion
cells for cleaning (Task 2) out of notebooks/02_profile_clean.ipynb.
"""


import pandas as pd

from src.clean import clean_freecodecamp


def test_clean_removes_duplicate_rows():
    df = pd.DataFrame({
        "source": ["freeCodeCamp", "freeCodeCamp"],
        "category": ["AI", "AI"],
        "title": ["Article 1", "Article 1"],
        "author": ["Author", "Author"],
        "publication_date": [
            "2026-01-01T10:00:00Z",
            "2026-01-01T10:00:00Z"
        ],
        "description": ["Description", "Description"],
        "url": [
            "https://example.com/1",
            "https://example.com/1"
        ],
        "topic": ["AI", "AI"],
        "matched_keywords": ["ai", "ai"]
    })

    result = clean_freecodecamp(df)

    assert len(result) == 1


def test_clean_removes_duplicate_urls():
    df = pd.DataFrame({
        "source": ["freeCodeCamp", "freeCodeCamp"],
        "category": ["AI", "AI"],
        "title": ["Article 1", "Article 2"],
        "author": ["Author 1", "Author 2"],
        "publication_date": [
            "2026-01-01T10:00:00Z",
            "2026-01-02T10:00:00Z"
        ],
        "description": ["Description 1", "Description 2"],
        "url": [
            "https://example.com/1",
            "https://example.com/1"
        ],
        "topic": ["AI", "AI"],
        "matched_keywords": ["ai", "machine learning"]
    })

    result = clean_freecodecamp(df)

    assert len(result) == 1
    assert result["url"].nunique() == 1


def test_clean_converts_publication_date():
    df = pd.DataFrame({
        "source": ["freeCodeCamp"],
        "category": ["AI"],
        "title": ["Article"],
        "author": ["Author"],
        "publication_date": ["2026-01-15T10:30:00Z"],
        "description": ["Description"],
        "url": ["https://example.com/1"],
        "topic": ["AI"],
        "matched_keywords": ["ai"]
    })

    result = clean_freecodecamp(df)

    assert pd.notna(result.loc[0, "publication_date"])
    assert "publication_datetime" in result.columns


def test_clean_fills_missing_keywords():
    df = pd.DataFrame({
        "source": ["freeCodeCamp"],
        "category": ["AI"],
        "title": ["Article"],
        "author": ["Author"],
        "publication_date": ["2026-01-15T10:30:00Z"],
        "description": ["Description"],
        "url": ["https://example.com/1"],
        "topic": ["AI"],
        "matched_keywords": [None]
    })

    result = clean_freecodecamp(df)

    assert result.loc[0, "matched_keywords"] == "none"
