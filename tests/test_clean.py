import pandas as pd

from src.clean import (
    combine_cleaned_sources,
    normalize_devto,
    normalize_freecodecamp,
    normalize_geeksforgeeks,
    normalize_medium,
    normalize_pluralsight,
    parse_tags,
)


# ============================================================
# TAG PARSING
# ============================================================

def test_parse_tags_list():

    result = parse_tags(
        ["AI", "Cloud"]
    )

    assert result == [
        "AI",
        "Cloud",
    ]


def test_parse_tags_string_list():

    result = parse_tags(
        "['AI', 'Cloud']"
    )

    assert result == [
        "AI",
        "Cloud",
    ]


def test_parse_tags_comma_string():

    result = parse_tags(
        "AI, Cloud"
    )

    assert result == [
        "AI",
        "Cloud",
    ]


# ============================================================
# DEV.TO
# ============================================================

def test_normalize_devto():

    df = pd.DataFrame(
        [
            {
                "title":
                    "Introduction to AI",

                "url":
                    "https://dev.to/example",

                "published_at":
                    "2026-01-01T12:00:00Z",

                "description":
                    "AI tutorial",

                "tag_list":
                    ["ai", "python"],

                "body_markdown":
                    "# Hello\nThis is AI.",

                "user":
                    {
                        "name": "Author"
                    },
            }
        ]
    )

    result = normalize_devto(
        df
    )

    row = result.iloc[0]

    assert (
        row["source"]
        == "dev.to"
    )

    assert (
        row["title"]
        == "Introduction to AI"
    )

    assert (
        row["author"]
        == "Author"
    )

    assert (
        row["publication_date"]
        == "2026-01-01"
    )

    assert (
        "Hello"
        in row["content"]
    )

    assert (
        row["tags"]
        == "ai, python"
    )


# ============================================================
# PLURALSIGHT
# ============================================================

def test_normalize_pluralsight():

    df = pd.DataFrame(
        [
            {
                "category":
                    "Cloud",

                "title":
                    "AWS Tutorial",

                "author":
                    "Sarah",

                "publication_date":
                    "2026-02-10",

                "description":
                    "Learn AWS",

                "url":
                    "https://pluralsight.com/example",

                "content":
                    "AWS cloud content",

                "tags":
                    ["AWS", "Cloud"],
            }
        ]
    )

    result = (
        normalize_pluralsight(
            df
        )
    )

    row = result.iloc[0]

    assert (
        row["source"]
        == "Pluralsight"
    )

    assert (
        row["category"]
        == "Cloud"
    )

    assert (
        row["content"]
        == "AWS cloud content"
    )

    assert (
        row["tags"]
        == "AWS, Cloud"
    )


# ============================================================
# FREECODECAMP
# ============================================================

def test_normalize_freecodecamp():

    df = pd.DataFrame(
        [
            {
                "topic":
                    "AI",

                "category":
                    "Python",

                "title":
                    "Python AI Tutorial",

                "author":
                    "Example Author",

                "publication_date":
                    "2026-03-01",

                "description":
                    "Learn AI",

                "url":
                    "https://freecodecamp.org/example",
            }
        ]
    )

    result = (
        normalize_freecodecamp(
            df
        )
    )

    row = result.iloc[0]

    assert (
        row["source"]
        == "freeCodeCamp"
    )

    assert (
        row["category"]
        == "AI"
    )

    assert (
        row["tags"]
        == "Python"
    )

    # Current scraper may not
    # contain full article content.
    assert (
        row["content"]
        == ""
    )


# ============================================================
# MEDIUM
# ============================================================

def test_normalize_medium():

    df = pd.DataFrame(
        [
            {
                "title":
                    "Machine Learning",

                "authors":
                    "Jane Doe",

                "timestamp":
                    "2026-04-01T10:00:00Z",

                "url":
                    "https://medium.com/example",

                "text":
                    "Machine learning article",

                "tags":
                    ["machine-learning", "ai"],

                "category":
                    "AI",
            }
        ]
    )

    result = normalize_medium(
        df
    )

    row = result.iloc[0]

    assert (
        row["source"]
        == "Medium"
    )

    assert (
        row["author"]
        == "Jane Doe"
    )

    assert (
        row["publication_date"]
        == "2026-04-01"
    )

    assert (
        row["content"]
        == "Machine learning article"
    )

    assert (
        row["tags"]
        == "machine-learning, ai"
    )


# ============================================================
# GEEKSFORGEEKS
# ============================================================

def test_normalize_geeksforgeeks():

    df = pd.DataFrame(
        [
            {
                "title":
                    "Pandas Tutorial",

                "url":
                    "https://geeksforgeeks.org/example",

                "content":
                    "Pandas dataframe tutorial",

                "tags":
                    "['Pandas', 'Python']",

                "category":
                    "Data",
            }
        ]
    )

    result = (
        normalize_geeksforgeeks(
            df
        )
    )

    row = result.iloc[0]

    assert (
        row["source"]
        == "GeeksforGeeks"
    )

    assert (
        row["category"]
        == "Data"
    )

    assert (
        row["content"]
        == "Pandas dataframe tutorial"
    )

    assert (
        row["tags"]
        == "Pandas, Python"
    )

    # The original dataset may
    # legitimately not contain author.
    assert (
        row["author"]
        == ""
    )


# ============================================================
# CROSS-SOURCE COMBINATION
# ============================================================

def test_cross_source_duplicate_urls():

    gfg = pd.DataFrame(
        [
            {
                "title":
                    "Article A",

                "url":
                    "https://example.com/article",

                "content":
                    "GFG content",

                "tags":
                    "Python",

                "category":
                    "Data",
            }
        ]
    )

    medium = pd.DataFrame(
        [
            {
                "title":
                    "Article B",

                "url":
                    "https://example.com/article",

                "text":
                    "Medium content",

                "tags":
                    ["AI"],

                "category":
                    "AI",

                "authors":
                    "Author",
            }
        ]
    )

    combined = (
        combine_cleaned_sources(
            {
                "GeeksforGeeks":
                    gfg,

                "Medium":
                    medium,
            }
        )
    )

    # Same URL should appear once.
    assert len(combined) == 1