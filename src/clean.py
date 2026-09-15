"""Task 2 (part 2) -- flatten each raw dev.to article onto the unified schema and clean it.

Moved here, unchanged in behaviour, from notebooks/02_profile_clean.ipynb.
"""

import re
from typing import Any

import pandas as pd

from .config import CLEANED_CSV_PATH


# ==============================================================================
# MARKDOWN / HTML / LIQUID CLEANUP
# ==============================================================================

# dev.to-flavoured Liquid/embed tags that show up in body_markdown.
_LIQUID_TAG_RE = re.compile(r"\{%.*?%\}", flags=re.DOTALL)
_CODE_FENCE_RE = re.compile(r"```.*?```", flags=re.DOTALL)
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_INLINE_CODE_RE = re.compile(r"`([^`]*)`")
_HEADING_RE = re.compile(r"^#{1,6}\s*", flags=re.MULTILINE)
_HR_RE = re.compile(r"^\s*-{3,}\s*$", flags=re.MULTILINE)
_BOLD_ITALIC_RE = re.compile(r"(\*\*|__)(.*?)\1|(\*|_)(.*?)\3", flags=re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_markdown_to_text(markdown):
    """Strips structural/markup noise out of a dev.to article's raw markdown, so the
    result is safe, readable plain text for NLP / keyword extraction downstream.
    """
    if not markdown:
        return ""
    text = markdown
    text = _LIQUID_TAG_RE.sub("", text)
    text = _CODE_FENCE_RE.sub("", text)
    text = _IMAGE_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _INLINE_CODE_RE.sub(r"\1", text)
    text = _HEADING_RE.sub("", text)
    text = _HR_RE.sub("", text)
    text = _BOLD_ITALIC_RE.sub(lambda m: m.group(2) or m.group(4) or "", text)
    text = _HTML_TAG_RE.sub("", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


# ==============================================================================
# FLATTEN: MAP EACH RAW ARTICLE ONTO THE PIPELINE'S UNIFIED SCHEMA
# ==============================================================================

def standardize_devto_article(raw: dict[str, Any]) -> dict[str, Any]:
    """Flattens one raw dev.to article dict onto the pipeline's unified content schema."""
    user = raw.get("user") or {}
    tag_list = raw.get("tag_list") or []
    if isinstance(tag_list, str):
        tag_list = [t.strip() for t in tag_list.split(",") if t.strip()]

    return {
        "external_id": f"devto:{raw.get('id')}",
        "title": (raw.get("title") or "").strip(),
        "source": "dev.to",
        "author": user.get("name") or user.get("username") or "",
        "published_date": raw.get("published_at") or raw.get("published_timestamp"),
        "url": raw.get("url"),
        "topic": tag_list[0] if tag_list else "",
        "tags": ", ".join(tag_list),
        "description": (raw.get("description") or "").strip(),
        "content_type": "article",
        "reading_time_minutes": raw.get("reading_time_minutes"),
        "reactions_count": raw.get("public_reactions_count"),
        "comments_count": raw.get("comments_count"),
        "cover_image": raw.get("cover_image"),
        # Carried straight over from Task 1's raw record -- cleaned up below.
        "content_markdown": raw.get("body_markdown"),
        "content_html": raw.get("body_html"),
        "content_clean": None,  # filled in below
    }


# ==============================================================================
# CLEAN: DTYPES, NULLS, DUPLICATES, TEXT/DATE STANDARDIZATION
# ==============================================================================

def flatten_and_clean(raw_records):
    """Runs the complete Task 2 flatten + clean pipeline on a list of raw article dicts."""
    standardized = [standardize_devto_article(r) for r in raw_records]
    df = pd.DataFrame(standardized)

    # Columns are already snake_case by construction; keep this explicit per the working rules.
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Drop duplicates: the same article can come back under more than one requested tag.
    before = len(df)
    df = df.drop_duplicates(subset="url").reset_index(drop=True)
    print(f"Dropped {before - len(df)} duplicate rows (same url, multiple tags)")

    # Quality filter: a record with no title or url is not usable downstream.
    df = df[df["title"].astype(bool) & df["url"].astype(bool)]

    # Dtypes / text / date standardisation.
    df["title"] = df["title"].str.strip()
    df["description"] = df["description"].fillna("").str.strip()
    df["tags"] = df["tags"].fillna("")
    df["published_date"] = pd.to_datetime(df["published_date"], errors="coerce", utc=True)
    df["reading_time_minutes"] = pd.to_numeric(df["reading_time_minutes"], errors="coerce").fillna(0).astype(int)
    df["reactions_count"] = pd.to_numeric(df["reactions_count"], errors="coerce").fillna(0).astype(int)
    df["comments_count"] = pd.to_numeric(df["comments_count"], errors="coerce").fillna(0).astype(int)

    # The whole point of this step: turn the raw markdown body into NLP-safe plain text.
    df["content_clean"] = df["content_markdown"].apply(clean_markdown_to_text)

    print("Cleaned shape:", df.shape)
    print("Rows with non-empty content_clean:", (df["content_clean"].str.len() > 0).sum())
    return df


def save_cleaned_data(df, path=CLEANED_CSV_PATH):
    """Saves the cleaned DataFrame to data/interim/cleaned.csv."""
    df.to_csv(path, index=False)
    print(f"Saved -> {path} ({len(df)} rows)")


def run_cleaning(raw_records):
    """Runs the complete Task 2 cleaning process and saves data/interim/cleaned.csv."""
    cleaned_df = flatten_and_clean(raw_records)
    save_cleaned_data(cleaned_df)
    return cleaned_df
