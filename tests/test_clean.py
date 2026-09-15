"""Tests for Task 2's cleaning logic (src/clean.py) -- moved here from the assertion
cells originally sketched in notebooks/02_profile_clean.ipynb, at the integration stage.
"""

from src.clean import clean_markdown_to_text, flatten_and_clean, standardize_devto_article


def test_clean_markdown_to_text_strips_liquid_and_html():
    markdown = (
        "# Heading\n\n"
        "{% embed https://example.com %}\n\n"
        "Some **bold** and _italic_ text with `inline code` and a "
        "[link](https://example.com) plus <b>raw html</b>.\n\n"
        "```python\nprint('code fence')\n```\n"
    )

    cleaned = clean_markdown_to_text(markdown)

    assert "{%" not in cleaned
    assert "<b>" not in cleaned
    assert "```" not in cleaned
    assert "link" in cleaned
    assert "bold" in cleaned and "italic" in cleaned


def test_clean_markdown_to_text_handles_empty_input():
    assert clean_markdown_to_text(None) == ""
    assert clean_markdown_to_text("") == ""


def test_standardize_devto_article_maps_fields():
    raw = {
        "id": 123,
        "title": "  Test Article  ",
        "user": {"name": "Jane Doe", "username": "janed"},
        "tag_list": ["ai", "python"],
        "published_at": "2026-01-01T00:00:00Z",
        "url": "https://dev.to/janed/test-article",
        "description": "A description",
        "reading_time_minutes": 5,
        "public_reactions_count": 10,
        "comments_count": 2,
        "body_markdown": "# Test\n\nSome content.",
        "body_html": "<h1>Test</h1>",
    }

    record = standardize_devto_article(raw)

    assert record["external_id"] == "devto:123"
    assert record["title"] == "Test Article"
    assert record["source"] == "dev.to"
    assert record["author"] == "Jane Doe"
    assert record["topic"] == "ai"
    assert record["tags"] == "ai, python"
    assert record["content_type"] == "article"


def test_standardize_devto_article_falls_back_to_username():
    raw = {"id": 1, "user": {"username": "janed"}, "tag_list": []}
    record = standardize_devto_article(raw)
    assert record["author"] == "janed"
    assert record["topic"] == ""
    assert record["tags"] == ""


def test_flatten_and_clean_drops_duplicate_urls():
    base = {
        "id": 1,
        "title": "Article One",
        "user": {"name": "A"},
        "published_at": "2026-01-01T00:00:00Z",
        "url": "https://dev.to/a/one",
        "description": "",
        "reading_time_minutes": 3,
        "public_reactions_count": 1,
        "comments_count": 0,
        "body_markdown": "Body one.",
        "body_html": "<p>Body one.</p>",
    }
    raw_records = [
        {**base, "tag_list": ["ai"]},
        # Same url, fetched under a second tag -- should be deduplicated.
        {**base, "tag_list": ["python"]},
    ]

    df = flatten_and_clean(raw_records)

    assert len(df) == 1
    assert df.iloc[0]["content_clean"] == "Body one."


def test_flatten_and_clean_drops_rows_with_no_title_or_url():
    raw_records = [
        {
            "id": 2, "title": "", "user": {"name": "A"}, "tag_list": ["ai"],
            "published_at": "2026-01-01T00:00:00Z", "url": "https://dev.to/a/two",
            "description": "", "reading_time_minutes": 1, "public_reactions_count": 0,
            "comments_count": 0, "body_markdown": "Body.", "body_html": "<p>Body.</p>",
        },
    ]

    df = flatten_and_clean(raw_records)

    assert len(df) == 0
