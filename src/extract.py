"""Task 1 -- dev.to (Forem) public Articles API client and extraction pipeline.

Moved here, unchanged in behaviour, from notebooks/01_extract.ipynb.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from .config import (
    CONTENT_DELAY,
    DEVTO_API_BASE,
    MAX_PAGES_PER_TAG,
    PER_PAGE,
    RAW_DIR,
    TAGS,
)


class DevToAPIError(RuntimeError):
    pass


@dataclass
class DevToClient:
    """Minimal client for the dev.to public API: pagination + retry/backoff on 429."""

    api_key: str | None = None
    base_url: str = DEVTO_API_BASE
    timeout: int = 15
    max_retries: int = 3
    backoff_seconds: float = 2.0

    def __post_init__(self):
        self.api_key = self.api_key or os.environ.get("DEVTO_API_KEY")
        self._session = requests.Session()
        headers = {"User-Agent": "edtech-content-pipeline/1.0"}
        if self.api_key:
            headers["api-key"] = self.api_key
        self._session.headers.update(headers)

    def _get(self, path: str, params: dict | None = None) -> list | dict:
        url = f"{self.base_url}{path}"
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 429:
                    time.sleep(self.backoff_seconds * attempt)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(self.backoff_seconds * attempt)
        raise DevToAPIError(f"GET {url} failed after {self.max_retries} attempts: {last_exc}")

    def get_articles(self, tag=None, page=1, per_page=30, top=None, username=None):
        """One page of articles."""
        params = {"page": page, "per_page": per_page}
        if tag:
            params["tag"] = tag
        if top:
            params["top"] = top
        if username:
            params["username"] = username
        data = self._get("/articles", params=params)
        return data if isinstance(data, list) else []

    def iter_articles_by_tag(self, tag, max_pages=5, per_page=30, top=None, sleep_between_pages=0.5):
        """Yields raw article dicts across multiple pages for a single tag."""
        for page in range(1, max_pages + 1):
            batch = self.get_articles(tag=tag, page=page, per_page=per_page, top=top)
            if not batch:
                break
            yield from batch
            if len(batch) < per_page:
                break
            time.sleep(sleep_between_pages)

    def get_article_by_id(self, article_id):
        """Full article, including body_markdown / body_html (listing endpoint never returns these)."""
        data = self._get(f"/articles/{article_id}")
        return data if isinstance(data, dict) else {}

    def get_articles_by_tags(self, tags, max_pages_per_tag=5, per_page=30, top=None):
        """Fetches and merges articles across several tags (raw, not deduped)."""
        results = []
        for tag in tags:
            results.extend(
                self.iter_articles_by_tag(tag=tag, max_pages=max_pages_per_tag, per_page=per_page, top=top)
            )
        return results


def fetch_full_content(client, raw_articles, delay=CONTENT_DELAY):
    """Merges body_markdown / body_html into each raw article dict, in place.

    The listing endpoint never returns the article body -- only GET /articles/{id} does.
    Nothing is cleaned or transformed here; text cleanup happens in clean.py (Task 2).
    """
    total = len(raw_articles)
    for i, article in enumerate(raw_articles, start=1):
        article_id = article.get("id")
        print(f"  [{i}/{total}] fetching full content for article {article_id}...", end="\r")
        try:
            detail = client.get_article_by_id(article_id)
            article["body_markdown"] = detail.get("body_markdown")
            article["body_html"] = detail.get("body_html")
        except Exception as exc:  # noqa: BLE001 - keep going even if one article fails
            print(f"\n  ! could not fetch content for article {article_id}: {exc}")
        time.sleep(delay)

    with_content = sum(1 for a in raw_articles if a.get("body_markdown"))
    print(f"\nDone -- {with_content}/{total} articles have body content")
    return raw_articles


def save_raw_articles(raw_articles, raw_dir=RAW_DIR):
    """Saves the raw API response, unmodified, as data/raw/devto_<date>.json."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    raw_path = raw_dir / f"devto_{timestamp}.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(raw_articles, f, ensure_ascii=False, indent=2)
    print(f"Saved raw response -> {raw_path}")
    return raw_path


def run_extraction(tags=TAGS, max_pages_per_tag=MAX_PAGES_PER_TAG, per_page=PER_PAGE):
    """Runs the complete Task 1 extraction process: listing + full content + save."""
    client = DevToClient()

    print(f"Fetching dev.to articles for tags={tags} (up to {max_pages_per_tag} pages each)...")
    raw_articles = client.get_articles_by_tags(tags=tags, max_pages_per_tag=max_pages_per_tag, per_page=per_page)
    print(f"-> {len(raw_articles)} raw articles fetched (listing only, no body yet)")

    fetch_full_content(client, raw_articles)

    raw_path = save_raw_articles(raw_articles)
    return raw_articles, raw_path
