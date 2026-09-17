"""
Source-specific normalization and shared cleaning.

Each source has a different raw structure.

This module converts all sources into:

source
category
title
author
publication_date
description
url
content
tags
"""

import ast
import re

import pandas as pd

from .config import COMMON_COLUMNS


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_text(value):
    """
    Convert a nullable value into clean text.
    """

    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def parse_tags(value):
    """
    Convert different tag representations into a Python list.

    Handles:

    ["AI", "Cloud"]

    "['AI', 'Cloud']"

    "AI, Cloud"
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(tag).strip()
            for tag in value
            if str(tag).strip()
        ]

    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if not text:
        return []

    # Try parsing a string representation of a list.
    try:

        parsed = ast.literal_eval(text)

        if isinstance(
            parsed,
            (list, tuple, set),
        ):

            return [
                str(tag).strip()
                for tag in parsed
                if str(tag).strip()
            ]

    except (
        ValueError,
        SyntaxError,
    ):
        pass

    # Otherwise assume comma-separated tags.
    return [
        tag.strip()
        for tag in text.split(",")
        if tag.strip()
    ]


def tags_to_string(value):
    """
    Store tags consistently in CSV-friendly form.
    """

    return ", ".join(
        parse_tags(value)
    )


def clean_text(value):
    """
    Perform conservative text cleanup.

    We intentionally avoid aggressive removal because programming
    articles may legitimately contain words such as code, output,
    example, syntax, etc.
    """

    text = safe_text(value)

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n",
        text,
    )

    return text.strip()


def normalize_date(value):
    """
    Convert valid dates/timestamps to YYYY-MM-DD.

    Missing or invalid dates remain blank rather than being invented.
    """

    text = safe_text(value)

    if not text:
        return ""

    parsed = pd.to_datetime(
        text,
        errors="coerce",
        utc=True,
    )

    if pd.isna(parsed):
        return ""

    return parsed.strftime(
        "%Y-%m-%d"
    )


# ============================================================
# DEV.TO
# ============================================================

def clean_devto_markdown(value):
    """
    Convert dev.to Markdown into cleaner plain text.

    Markup is removed conservatively while retaining the
    educational article text.
    """

    text = safe_text(value)

    if not text:
        return ""

    # Liquid/embed tags
    text = re.sub(
        r"\{%.*?%\}",
        "",
        text,
        flags=re.DOTALL,
    )

    # Markdown images
    text = re.sub(
        r"!\[[^\]]*\]\([^)]*\)",
        "",
        text,
    )

    # Markdown links: retain visible text.
    text = re.sub(
        r"\[([^\]]+)\]\([^)]*\)",
        r"\1",
        text,
    )

    # Inline code: retain code text.
    text = re.sub(
        r"`([^`]*)`",
        r"\1",
        text,
    )

    # Heading markers
    text = re.sub(
        r"^#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE,
    )

    # HTML tags
    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    return clean_text(text)


def normalize_devto(
    df: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

        user = raw.get("user") or {}

        tag_value = (
            raw.get("tag_list")
            or raw.get("tags")
        )

        tag_list = parse_tags(
            tag_value
        )

        category = safe_text(
            raw.get("category")
            or raw.get("topic")
        )

        # If no explicit category exists,
        # use the first available tag.
        if not category and tag_list:
            category = tag_list[0]

        content = (
            raw.get("body_markdown")
            or raw.get("content_markdown")
            or raw.get("content_clean")
            or ""
        )

        records.append(
            {
                "source": "dev.to",

                "category": category,

                "title": safe_text(
                    raw.get("title")
                ),

                "author": safe_text(
                    user.get("name")
                    or user.get("username")
                    or raw.get("author")
                ),

                "publication_date":
                    normalize_date(
                        raw.get("published_at")
                        or raw.get(
                            "published_timestamp"
                        )
                    ),

                "description":
                    clean_text(
                        raw.get("description")
                    ),

                "url": safe_text(
                    raw.get("url")
                ),

                "content":
                    clean_devto_markdown(
                        content
                    ),

                "tags":
                    tags_to_string(
                        tag_list
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# PLURALSIGHT
# ============================================================

def normalize_pluralsight(
    df: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

        records.append(
            {
                "source": "Pluralsight",

                "category": safe_text(
                    raw.get("category")
                ),

                "title": safe_text(
                    raw.get("title")
                ),

                "author": safe_text(
                    raw.get("author")
                ),

                "publication_date":
                    normalize_date(
                        raw.get(
                            "publication_date"
                        )
                    ),

                "description":
                    clean_text(
                        raw.get("description")
                    ),

                "url": safe_text(
                    raw.get("url")
                ),

                "content":
                    clean_text(
                        raw.get("content")
                    ),

                "tags":
                    tags_to_string(
                        raw.get("tags")
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# FREECODECAMP
# ============================================================

def normalize_freecodecamp(
    df: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

        # Dana's pipeline uses topic for the
        # AI / Cloud / Data Science grouping.
        category = safe_text(
            raw.get("topic")
            or raw.get("category")
        )

        records.append(
            {
                "source": "freeCodeCamp",

                "category": category,

                "title": safe_text(
                    raw.get("title")
                ),

                "author": safe_text(
                    raw.get("author")
                ),

                "publication_date":
                    normalize_date(
                        raw.get(
                            "publication_date"
                        )
                    ),

                "description":
                    clean_text(
                        raw.get("description")
                    ),

                "url": safe_text(
                    raw.get("url")
                ),

                # Current freeCodeCamp extractor
                # may not contain article body.
                "content":
                    clean_text(
                        raw.get("content")
                    ),

                # Preserve the site's category/tag.
                "tags":
                    tags_to_string(
                        raw.get("category")
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# MEDIUM
# ============================================================

def normalize_medium(
    df: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

        publication_date = (
            raw.get("publication_date")
            or raw.get("timestamp")
        )

        content = (
            raw.get("content")
            or raw.get("text")
        )

        author = (
            raw.get("author")
            or raw.get("authors")
        )

        records.append(
            {
                "source": "Medium",

                "category": safe_text(
                    raw.get("category")
                ),

                "title": safe_text(
                    raw.get("title")
                ),

                "author": safe_text(
                    author
                ),

                "publication_date":
                    normalize_date(
                        publication_date
                    ),

                "description":
                    clean_text(
                        raw.get("description")
                    ),

                "url": safe_text(
                    raw.get("url")
                ),

                "content":
                    clean_text(
                        content
                    ),

                "tags":
                    tags_to_string(
                        raw.get("tags")
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# GEEKSFORGEEKS
# ============================================================

def normalize_geeksforgeeks(
    df: pd.DataFrame,
) -> pd.DataFrame:

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

        records.append(
            {
                "source":
                    "GeeksforGeeks",

                "category":
                    safe_text(
                        raw.get("category")
                    ),

                "title":
                    safe_text(
                        raw.get("title")
                    ),

                # Original Kaggle source does
                # not reliably provide author.
                "author":
                    safe_text(
                        raw.get("author")
                    ),

                # Same for publication date.
                "publication_date":
                    normalize_date(
                        raw.get(
                            "publication_date"
                        )
                    ),

                "description":
                    clean_text(
                        raw.get("description")
                    ),

                "url":
                    safe_text(
                        raw.get("url")
                    ),

                "content":
                    clean_text(
                        raw.get("content")
                    ),

                "tags":
                    tags_to_string(
                        raw.get("tags")
                    ),
            }
        )

    return pd.DataFrame(
        records
    )


# ============================================================
# NORMALIZER REGISTRY
# ============================================================

NORMALIZERS = {
    "dev.to":
        normalize_devto,

    "Pluralsight":
        normalize_pluralsight,

    "freeCodeCamp":
        normalize_freecodecamp,

    "Medium":
        normalize_medium,

    "GeeksforGeeks":
        normalize_geeksforgeeks,
}


# ============================================================
# SHARED CLEANING
# ============================================================

def clean_source_dataframe(
    source: str,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize and clean one source.
    """

    if source not in NORMALIZERS:

        raise ValueError(
            f"Unsupported source: {source}"
        )

    cleaned = NORMALIZERS[source](
        df
    ).copy()

    # Guarantee common columns exist.
    for column in COMMON_COLUMNS:

        if column not in cleaned.columns:
            cleaned[column] = ""

    cleaned = cleaned[
        COMMON_COLUMNS
    ]

    # Standardize text/null handling.
    for column in COMMON_COLUMNS:

        cleaned[column] = (
            cleaned[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # A record without title or URL is not
    # useful for this content dataset.
    cleaned = cleaned[
        cleaned["title"].ne("")
        & cleaned["url"].ne("")
    ].copy()

    # Remove repeated articles from a source.
    cleaned = (
        cleaned
        .drop_duplicates(
            subset=["url"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return cleaned


# ============================================================
# CROSS-SOURCE COMBINATION
# ============================================================

def combine_cleaned_sources(
    source_frames,
) -> pd.DataFrame:
    """
    Normalize every source and vertically concatenate them.

    This is a UNION/CONCAT operation rather than a relational join,
    because unrelated articles do not share a meaningful join key.
    """

    cleaned_frames = []

    for source, df in source_frames.items():

        print(
            f"Cleaning {source}..."
        )

        cleaned = (
            clean_source_dataframe(
                source,
                df,
            )
        )

        print(
            f"{source}: "
            f"{len(cleaned)} cleaned records"
        )

        cleaned_frames.append(
            cleaned
        )

    if not cleaned_frames:

        return pd.DataFrame(
            columns=COMMON_COLUMNS
        )

    combined = pd.concat(
        cleaned_frames,
        ignore_index=True,
        sort=False,
    )

    before = len(combined)

    # Cross-source duplicate protection.
    combined = (
        combined
        .drop_duplicates(
            subset=["url"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    removed = (
        before - len(combined)
    )

    print(
        f"Cross-source duplicates removed: "
        f"{removed}"
    )

    return combined