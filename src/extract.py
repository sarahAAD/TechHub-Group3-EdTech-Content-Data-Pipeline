"""
Unified extraction layer.

Collects data from:

1. dev.to          -> public API
2. Pluralsight     -> web scraping
3. freeCodeCamp    -> Playwright
4. Medium          -> Hugging Face
5. GeeksforGeeks   -> Kaggle

By default, previously known URLs are skipped using persistent ADLS state.

Use refresh=True to ignore known-URL state for the selected extraction.
"""

from __future__ import annotations

import ast
import csv
import datetime
import hashlib
import json
import os
import re
import signal
import time
from pathlib import Path
from urllib.parse import (
    urljoin,
    urlparse,
)

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .config import (
    AI_KEYWORDS,
    CLOUD_KEYWORDS,
    DATA_KEYWORDS,

    DEVTO_API_BASE,
    DEVTO_CONTENT_DELAY,
    DEVTO_MAX_PAGES_PER_TAG,
    DEVTO_PER_PAGE,
    DEVTO_TAGS,

    FREECODECAMP_BASE_SEARCH_URL,
    FREECODECAMP_CLICKS_PER_TERM,
    FREECODECAMP_REQUEST_DELAY,
    FREECODECAMP_SEARCH_TERMS,
    FREECODECAMP_TARGET_ARTICLES_PER_TERM,

    GFG_DATASET_ID,
    GFG_OUTPUT,

    MEDIUM_DATASET_ID,
    MEDIUM_OUTPUT,

    PLURALSIGHT_BASE_URL,
    PLURALSIGHT_CATEGORIES,
    PLURALSIGHT_HEADERS,
    PLURALSIGHT_MAX_ARTICLES,
    PLURALSIGHT_REQUEST_DELAY,
    PLURALSIGHT_REQUEST_TIMEOUT,

    RAW_DIR,
    RAW_PATTERNS,
    SUPPORTED_SOURCES,
)

from .upload import (
    load_known_urls_from_adls,
    save_known_urls_to_adls,
)


# ============================================================
# SHARED HELPERS
# ============================================================

def matches_keyword(
    text,
    keyword,
):
    """
    Match a keyword using word boundaries.

    This prevents short terms such as AI from matching
    arbitrary substrings.
    """

    text = str(
        text or ""
    ).lower()

    pattern = (
        r"(?<!\w)"
        + re.escape(
            keyword.lower()
        )
        + r"(?!\w)"
    )

    return (
        re.search(
            pattern,
            text,
        )
        is not None
    )


def classify_topic(text):
    """
    Classify content into AI, Data or Cloud.

    Returns None when no project topic matches.
    """

    for keyword in AI_KEYWORDS:

        if matches_keyword(
            text,
            keyword,
        ):
            return "AI"

    for keyword in DATA_KEYWORDS:

        if matches_keyword(
            text,
            keyword,
        ):
            return "Data"

    for keyword in CLOUD_KEYWORDS:

        if matches_keyword(
            text,
            keyword,
        ):
            return "Cloud"

    return None


def detect_matched_keywords(text):
    """
    Return all AI/Data/Cloud keywords found in text.
    """

    keywords = (
        AI_KEYWORDS
        + DATA_KEYWORDS
        + CLOUD_KEYWORDS
    )

    return [
        keyword
        for keyword in keywords
        if matches_keyword(
            text,
            keyword,
        )
    ]


def save_json(
    records,
    path,
):
    """
    Save records as UTF-8 JSON.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            records,
            file,
            ensure_ascii=False,
            indent=2,
        )


def compute_content_hash(text):
    """
    هاش md5 بسيط للمحتوى. مو للأمان - بس عشان نقارن بسرعة هل
    نفس الرابط تغيّر محتواه بين batch وبعده.
    """

    return hashlib.md5(
        (text or "").encode("utf-8")
    ).hexdigest()


def build_seen_map(
    records,
    url_key="url",
    content_fn=None,
):
    """
    يبني dict {url: signature} من قائمة records جاهزة، عشان نحفظه
    كـ"قائمة روابط معروفة" لهالمصدر بعد كل batch ناجح (راجع
    upload.save_known_urls_to_adls).

    لو content_fn معطى: نخزن هاش المحتوى (نقدر نكتشف "تغيّر"
    حقيقي فيما بعد، مو بس "جديد").
    لو مو معطى: نخزن بس "seen" (يكفي لتفادي إعادة الجلب لمصادر
    جلب المحتوى فيها مكلف، بس ما يكتشف تعديل بمقالة سبق شفناها).
    """

    seen = {}

    for record in records:

        url = record.get(url_key)

        if not url:
            continue

        seen[url] = (
            compute_content_hash(
                content_fn(record)
            )
            if content_fn
            else "seen"
        )

    return seen


# ============================================================
# DEV.TO EXTRACTION
# ============================================================

class DevToClient:

    def __init__(
        self,
        api_key=None,
    ):

        self.api_key = (
            api_key
            or os.environ.get(
                "DEVTO_API_KEY"
            )
        )

        self.session = (
            requests.Session()
        )

        headers = {
            "User-Agent":
                "edtech-content-pipeline/1.0"
        }

        if self.api_key:

            headers[
                "api-key"
            ] = self.api_key

        self.session.headers.update(
            headers
        )


    def get(
        self,
        path,
        params=None,
        max_retries=3,
    ):

        url = (
            f"{DEVTO_API_BASE}"
            f"{path}"
        )

        last_error = None

        for attempt in range(
            1,
            max_retries + 1,
        ):

            try:

                response = (
                    self.session.get(
                        url,
                        params=params,
                        timeout=30,
                    )
                )

                if (
                    response.status_code
                    == 429
                ):

                    wait = (
                        2 * attempt
                    )

                    print(
                        "dev.to rate limit. "
                        f"Waiting {wait}s..."
                    )

                    time.sleep(wait)

                    continue

                response.raise_for_status()

                return response.json()

            except (
                requests.RequestException
            ) as error:

                last_error = error

                time.sleep(
                    2 * attempt
                )

        raise RuntimeError(
            "dev.to request failed: "
            f"{last_error}"
        )


    def get_articles(
        self,
        tag,
        page,
    ):

        result = self.get(
            "/articles",
            params={
                "tag": tag,
                "page": page,
                "per_page":
                    DEVTO_PER_PAGE,
            },
        )

        if isinstance(
            result,
            list,
        ):
            return result

        return []


    def get_article(
        self,
        article_id,
    ):

        result = self.get(
            f"/articles/{article_id}"
        )

        if isinstance(
            result,
            dict,
        ):
            return result

        return {}


def extract_devto(
    refresh=False,
):

    client = DevToClient()

    articles_by_id = {}

    for tag in DEVTO_TAGS:

        print(
            f"dev.to tag: {tag}"
        )

        for page in range(
            1,
            DEVTO_MAX_PAGES_PER_TAG
            + 1,
        ):

            batch = (
                client.get_articles(
                    tag,
                    page,
                )
            )

            if not batch:
                break

            for article in batch:

                article_id = (
                    article.get("id")
                )

                if article_id:

                    articles_by_id[
                        article_id
                    ] = article

            if (
                len(batch)
                < DEVTO_PER_PAGE
            ):
                break

    articles = list(
        articles_by_id.values()
    )

    print(
        f"dev.to unique articles: "
        f"{len(articles)}"
    )

    # فلترة الجديد/المتغيّر بالـ URL: قبل ما نجيب تفاصيل أي مقالة
    # (اللي هي الجزء المكلف - طلب شبكة إضافي لكل مقالة)، نتجاهل
    # أي رابط سبق استخرجناه بـ batch سابق.
    known_urls = (
        {}
        if refresh
        else load_known_urls_from_adls(
            "dev.to"
        )
    )

    if known_urls:

        before_count = len(articles)

        articles = [
            article
            for article in articles
            if article.get("url")
            not in known_urls
        ]

        print(
            f"dev.to: {before_count - len(articles)} "
            "مقالة معروفة من batch سابق، "
            "بنتخطى جلب تفاصيلها. "
            f"الجديد: {len(articles)}"
        )

    for index, article in enumerate(
        articles,
        start=1,
    ):

        article_id = (
            article.get("id")
        )

        print(
            f"dev.to content "
            f"{index}/{len(articles)}",
            end="\r",
        )

        try:

            detail = (
                client.get_article(
                    article_id
                )
            )

            article[
                "body_markdown"
            ] = detail.get(
                "body_markdown"
            )

            article[
                "body_html"
            ] = detail.get(
                "body_html"
            )

        except ExtractionTimeout:
            raise

        except Exception as error:

            print(
                "\nCould not fetch "
                f"dev.to article "
                f"{article_id}: "
                f"{error}"
            )

        time.sleep(
            DEVTO_CONTENT_DELAY
        )

    today = (
        datetime.date.today()
        .isoformat()
    )

    output = (
        RAW_DIR
        / f"devto_{today}.json"
    )

    save_json(
        articles,
        output,
    )

    print(
        f"\ndev.to saved: "
        f"{output}"
    )

    save_known_urls_to_adls(
        "dev.to",
        build_seen_map(
            articles,
            url_key="url",
        ),
    )

    return output


# ============================================================
# PLURALSIGHT EXTRACTION
# ============================================================

pluralsight_session = (
    requests.Session()
)

pluralsight_session.headers.update(
    PLURALSIGHT_HEADERS
)


def fetch_pluralsight_page(
    url,
):

    try:

        response = (
            pluralsight_session.get(
                url,
                timeout=
                    PLURALSIGHT_REQUEST_TIMEOUT,
            )
        )

        print(
            f"GET {url} -> "
            f"{response.status_code}"
        )

        if (
            response.status_code
            == 200
        ):

            time.sleep(
                PLURALSIGHT_REQUEST_DELAY
            )

            return response.text

        if (
            response.status_code
            == 429
        ):

            print(
                "Rate limited. "
                "Waiting 10 seconds..."
            )

            time.sleep(10)

    except (
        requests.RequestException
    ) as error:

        print(
            f"Request error: "
            f"{error}"
        )

    return None


def normalize_pluralsight_url(
    url,
):

    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path.rstrip('/')}"
    )


def extract_pluralsight_links(
    html,
    category_url,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = set()

    category_path = (
        urlparse(
            category_url
        ).path.rstrip("/")
        + "/"
    )

    for anchor in soup.find_all(
        "a",
        href=True,
    ):

        url = urljoin(
            PLURALSIGHT_BASE_URL,
            anchor["href"],
        )

        url = (
            normalize_pluralsight_url(
                url
            )
        )

        if (
            urlparse(url)
            .path
            .startswith(
                category_path
            )
        ):
            links.add(url)

    return links


def discover_pluralsight_urls(
    category_url,
    max_pages,
):

    article_urls = set()

    for page in range(
        1,
        max_pages + 1,
    ):

        if (
            len(article_urls)
            >= PLURALSIGHT_MAX_ARTICLES
        ):
            break

        page_url = (
            category_url
            if page == 1
            else (
                f"{category_url}"
                f"?page={page}"
            )
        )

        print(
            f"Scanning Pluralsight "
            f"page {page}..."
        )

        html = (
            fetch_pluralsight_page(
                page_url
            )
        )

        if not html:
            continue

        article_urls.update(
            extract_pluralsight_links(
                html,
                category_url,
            )
        )

    return sorted(
        article_urls
    )[
        :PLURALSIGHT_MAX_ARTICLES
    ]


def parse_pluralsight_article(
    url,
    html,
    category,
):

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for element in soup.find_all(
        [
            "nav",
            "header",
            "footer",
            "aside",
            "script",
            "style",
        ]
    ):
        element.decompose()

    title = ""

    h1 = soup.find("h1")

    if h1:

        title = h1.get_text(
            " ",
            strip=True,
        )

    description = ""

    meta_description = soup.find(
        "meta",
        attrs={
            "name": "description"
        },
    )

    if meta_description:

        description = (
            meta_description.get(
                "content",
                "",
            ).strip()
        )

    author = ""

    meta_author = soup.find(
        "meta",
        attrs={
            "name": "author"
        },
    )

    if meta_author:

        author = (
            meta_author.get(
                "content",
                "",
            ).strip()
        )

    publication_date = ""

    date_element = soup.find(
        "p",
        class_="date-length-text",
    )

    if date_element:

        publication_date = (
            date_element
            .get_text(
                " ",
                strip=True,
            )
            .split("•")[0]
            .strip()
        )

    tags = []

    tag_list = soup.find(
        "ul",
        class_="tag-list-listing",
    )

    if tag_list:

        tags = [
            item.get_text(
                " ",
                strip=True,
            )
            for item
            in tag_list.find_all(
                "li"
            )
            if item.get_text(
                strip=True
            )
        ]

    content_area = (
        soup.find("article")
        or soup.find("main")
        or soup.body
    )

    content_parts = []

    if content_area:

        for element in (
            content_area.find_all(
                [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "p",
                    "li",
                ]
            )
        ):

            text = element.get_text(
                " ",
                strip=True,
            )

            if not text:
                continue

            skip_phrases = [
                "Minute Read",
                "Read article",
                "Table of Contents",
                "Copyright ©",
                "Terms of Use",
                "Privacy Policy",
                "Advance your tech skills today",
                "Subscribe to the newsletter",
                "Free individual trial",
            ]

            if any(
                phrase in text
                for phrase
                in skip_phrases
            ):
                continue

            if text.startswith(
                "By "
            ):
                continue

            content_parts.append(
                text
            )

    content = "\n\n".join(
        content_parts
    ).strip()

    return {
        "source":
            "Pluralsight",

        "category":
            category,

        "title":
            title,

        "author":
            author,

        "publication_date":
            publication_date,

        "description":
            description,

        "tags":
            tags,

        "url":
            url,

        "content":
            content,

        "scraped_at":
            datetime.datetime.now()
            .isoformat(),
    }


def extract_pluralsight(
    refresh=False,
):

    known_urls = (
        {}
        if refresh
        else load_known_urls_from_adls(
            "Pluralsight"
        )
    )

    seen_this_run = {}

    outputs = []

    for (
        category_name,
        category_config,
    ) in (
        PLURALSIGHT_CATEGORIES.items()
    ):

        output = Path(
            category_config[
                "output"
            ]
        )

        outputs.append(output)

        article_urls = (
            discover_pluralsight_urls(
                category_config["url"],
                category_config[
                    "max_pages"
                ],
            )
        )

        # فلترة الجديد/المتغيّر بالـ URL: قبل ما نجيب صفحة أي
        # مقالة كاملة (الجزء المكلف)، نتجاهل أي رابط سبق
        # استخرجناه بـ batch سابق.
        if known_urls:

            before_count = len(
                article_urls
            )

            article_urls = [
                url
                for url in article_urls
                if url not in known_urls
            ]

            print(
                f"Pluralsight {category_name}: "
                f"{before_count - len(article_urls)} "
                "رابط معروف من batch سابق، "
                "بنتخطاه. الجديد: "
                f"{len(article_urls)}"
            )

        results = []

        for index, url in enumerate(
            article_urls,
            start=1,
        ):

            print(
                f"Pluralsight "
                f"{category_name}: "
                f"{index}/"
                f"{len(article_urls)}"
            )

            html = (
                fetch_pluralsight_page(
                    url
                )
            )

            if not html:
                continue

            record = (
                parse_pluralsight_article(
                    url,
                    html,
                    category_name,
                )
            )

            if record["content"]:

                results.append(
                    record
                )

                # Incremental save.
                save_json(
                    results,
                    output,
                )

        print(
            f"{category_name}: "
            f"{len(results)} saved"
        )

        seen_this_run.update(
            build_seen_map(
                results,
                url_key="url",
            )
        )

    save_known_urls_to_adls(
        "Pluralsight",
        seen_this_run,
    )

    return outputs


# ============================================================
# FREECODECAMP EXTRACTION
# ============================================================

def extract_freecodecamp(
    refresh=False,
):

    try:

        from playwright.sync_api import (
            sync_playwright,
        )

    except ImportError as error:

        raise RuntimeError(
            "Playwright is required for "
            "freeCodeCamp extraction. "
            "Run: pip install playwright "
            "and then "
            "playwright install chromium"
        ) from error

    results = []

    seen_urls = set()

    known_urls = (
        {}
        if refresh
        else load_known_urls_from_adls(
            "freeCodeCamp"
        )
    )

    skipped_known = 0

    with sync_playwright() as p:

        browser = (
            p.chromium.launch(
                headless=True,
                args=[
                    "--disable-dev-shm-usage",
                ],
            )
        )

        page = browser.new_page()

        for (
            topic,
            search_term,
        ) in (
            FREECODECAMP_SEARCH_TERMS
            .items()
        ):

            search_url = (
                FREECODECAMP_BASE_SEARCH_URL
                .format(
                    search_term
                )
            )

            print(
                f"freeCodeCamp: "
                f"{search_url}"
            )

            page.goto(
                search_url,
                wait_until=
                    "networkidle",
            )

            for _ in range(
                FREECODECAMP_CLICKS_PER_TERM
            ):

                try:

                    page.click(
                        "#readMoreBtn",
                        timeout=5000,
                    )

                    page.wait_for_timeout(
                        2000
                    )

                except ExtractionTimeout:
                    raise

                except Exception:
                    break

            soup = BeautifulSoup(
                page.content(),
                "html.parser",
            )

            cards = soup.find_all(
                "article",
                class_="post-card",
            )

            collected = 0

            for card in cards:

                if (
                    collected
                    >= FREECODECAMP_TARGET_ARTICLES_PER_TERM
                ):
                    break

                link_tag = card.find(
                    "a",
                    class_=
                        "post-card-image-link",
                )

                if not link_tag:
                    continue

                href = link_tag.get(
                    "href"
                )

                if not href:
                    continue

                url = (
                    href
                    if href.startswith(
                        "http"
                    )
                    else (
                        "https://www."
                        "freecodecamp.org"
                        + href
                    )
                )

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                # فلترة الجديد/المتغيّر بالـ URL: قبل ما نفتح صفحة
                # المقالة كاملة (page.goto - الجزء المكلف)، نتجاهل
                # أي رابط سبق استخرجناه بـ batch سابق.
                if (
                    known_urls
                    and url in known_urls
                ):
                    skipped_known += 1
                    continue

                author_tag = card.find(
                    "a",
                    class_="meta-item",
                )

                listing_author = (
                    author_tag.get_text(
                        " ",
                        strip=True,
                    )
                    if author_tag
                    else ""
                )

                site_tag = card.find(
                    "span",
                    class_="post-card-tags",
                )

                site_category = ""

                if site_tag:

                    category_link = (
                        site_tag.find("a")
                    )

                    if category_link:

                        site_category = (
                            category_link
                            .get_text(
                                " ",
                                strip=True,
                            )
                        )

                try:

                    page.goto(
                        url,
                        wait_until=
                            "networkidle",
                    )

                    article_soup = (
                        BeautifulSoup(
                            page.content(),
                            "html.parser",
                        )
                    )

                    h1 = (
                        article_soup
                        .find("h1")
                    )

                    title = (
                        h1.get_text(
                            " ",
                            strip=True,
                        )
                        if h1
                        else ""
                    )

                    date_meta = (
                        article_soup.find(
                            "meta",
                            attrs={
                                "property":
                                    "article:"
                                    "published_time"
                            },
                        )
                    )

                    publication_date = (
                        date_meta.get(
                            "content",
                            "",
                        )
                        if date_meta
                        else ""
                    )

                    description_meta = (
                        article_soup.find(
                            "meta",
                            attrs={
                                "name":
                                    "description"
                            },
                        )
                    )

                    description = (
                        description_meta.get(
                            "content",
                            "",
                        )
                        if description_meta
                        else ""
                    )

                    # Full article body.
                    article_body = (
                        article_soup.find(
                            "article"
                        )
                        or article_soup.find(
                            "main"
                        )
                    )

                    content = ""

                    if article_body:

                        for unwanted in (
                            article_body.find_all(
                                [
                                    "script",
                                    "style",
                                    "nav",
                                    "aside",
                                ]
                            )
                        ):
                            unwanted.decompose()

                        content = (
                            article_body.get_text(
                                "\n",
                                strip=True,
                            )
                        )

                    search_text = " ".join(
                        [
                            title,
                            description,
                            site_category,
                        ]
                    )

                    matched = (
                        detect_matched_keywords(
                            search_text
                        )
                    )

                    results.append(
                        {
                            "source":
                                "freeCodeCamp",

                            "category":
                                site_category,

                            "title":
                                title,

                            "author":
                                listing_author,

                            "publication_date":
                                publication_date,

                            "description":
                                description,

                            "url":
                                url,

                            "topic":
                                topic,

                            "matched_keywords":
                                ", ".join(
                                    matched
                                ),

                            "content":
                                content,
                        }
                    )

                    collected += 1

                    print(
                        f"[{topic}] "
                        f"{collected}/"
                        f"{FREECODECAMP_TARGET_ARTICLES_PER_TERM}"
                    )

                except ExtractionTimeout:
                    raise

                except Exception as error:

                    print(
                        "freeCodeCamp failed: "
                        f"{url}: {error}"
                    )

                time.sleep(
                    FREECODECAMP_REQUEST_DELAY
                )

        browser.close()

    if skipped_known:

        print(
            f"freeCodeCamp: {skipped_known} "
            "مقالة معروفة من batch سابق، "
            "اتخطينا فتح صفحتها كاملة."
        )

    today = (
        datetime.date.today()
        .isoformat()
    )

    output = (
        RAW_DIR
        / (
            "freecodecamp_"
            f"{today}.csv"
        )
    )

    fieldnames = [
        "source",
        "category",
        "title",
        "author",
        "publication_date",
        "description",
        "url",
        "topic",
        "matched_keywords",
        "content",
    ]

    with output.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    print(
        "freeCodeCamp saved: "
        f"{output}"
    )

    save_known_urls_to_adls(
        "freeCodeCamp",
        build_seen_map(
            results,
            url_key="url",
        ),
    )

    return output


# ============================================================
# MEDIUM EXTRACTION
# ============================================================

def parse_medium_tags(
    value,
):

    if isinstance(
        value,
        list,
    ):
        return value

    if value is None:
        return []

    try:

        parsed = (
            ast.literal_eval(
                str(value)
            )
        )

        if isinstance(
            parsed,
            list,
        ):
            return parsed

    except (
        ValueError,
        SyntaxError,
    ):
        pass

    return [
        str(value)
    ]


def extract_medium(
    refresh=False,
):

    try:

        from datasets import (
            load_dataset,
        )

    except ImportError as error:

        raise RuntimeError(
            "datasets is required for "
            "Medium extraction."
        ) from error

    print(
        "Downloading Medium dataset..."
    )

    dataset = load_dataset(
        MEDIUM_DATASET_ID,
        split="train",
    )

    # ملاحظة: كنا نستخدم dataset.to_pandas() ثم
    # df.to_dict(orient="records") قبل هذا السطر، وهذا كان
    # يسوي نسختين كاملتين إضافيتين لكل بيانات Medium (اللي
    # فيها نص المقالات كاملة لـ 171 ألف صف) بالذاكرة، وهذا
    # هو السبب الحقيقي وراء انقطاع الحاوية بـ OOM (exit code
    # 137). التكرار المباشر على dataset يرجع كل صف كـ dict
    # مباشرة من صيغة Arrow الموفرة للذاكرة، بدون أي نسخ
    # إضافية لكل البيانات.

    # فلترة الجديد/المتغيّر بالـ URL: هنا المحتوى يجي مجاني مع
    # تكرار الـ dataset (مافيه طلب شبكة إضافي لكل مقالة زي
    # dev.to/Pluralsight/freeCodeCamp)، فنقدر نسوي مقارنة حقيقية
    # بهاش المحتوى ونكتشف "تغيّر" فعلي، مو بس "جديد".
    known_urls = (
        {}
        if refresh
        else load_known_urls_from_adls(
            "Medium"
        )
    )

    skipped_unchanged = 0

    records = []

    for raw in dataset:

        title = str(
            raw.get("title")
            or ""
        )

        tags = parse_medium_tags(
            raw.get("tags")
        )

        search_text = " ".join(
            [
                title,
                " ".join(
                    str(tag)
                    for tag in tags
                ),
            ]
        )

        category = (
            classify_topic(
                search_text
            )
        )

        if not category:
            continue

        url = raw.get("url")
        content = raw.get("text")

        if (
            known_urls
            and known_urls.get(url)
            == compute_content_hash(
                content
            )
        ):
            skipped_unchanged += 1
            continue

        records.append(
            {
                "source":
                    "Medium",

                "category":
                    category,

                "title":
                    title,

                "author":
                    raw.get(
                        "authors"
                    ),

                "publication_date":
                    raw.get(
                        "timestamp"
                    ),

                "description":
                    "",

                "url":
                    url,

                "content":
                    content,

                "tags":
                    tags,
            }
        )

    save_json(
        records,
        MEDIUM_OUTPUT,
    )

    print(
        f"Medium saved: "
        f"{len(records)} records "
        "(جديد/متغيّر). تخطينا "
        f"{skipped_unchanged} مقالة "
        "معروفة وما تغيرت."
    )

    save_known_urls_to_adls(
        "Medium",
        build_seen_map(
            records,
            url_key="url",
            content_fn=lambda record: (
                record.get("content")
            ),
        ),
    )

    return MEDIUM_OUTPUT


# ============================================================
# GEEKSFORGEEKS EXTRACTION
# ============================================================

def load_gfg_csv(
    folder,
):

    csv_files = list(
        Path(folder).rglob(
            "*.csv"
        )
    )

    if not csv_files:

        raise FileNotFoundError(
            "No CSV found in "
            "GeeksforGeeks dataset."
        )

    frames = []

    for file in csv_files:

        try:

            df = pd.read_csv(
                file,
                encoding="utf-8",
                low_memory=False,
            )

        except UnicodeDecodeError:

            print(
                f"UTF-8 failed for "
                f"{file.name}; "
                "trying latin-1."
            )

            df = pd.read_csv(
                file,
                encoding="latin-1",
                low_memory=False,
            )

        frames.append(df)

    return pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )


def extract_geeksforgeeks(
    refresh=False,
):

    try:

        import kagglehub

    except ImportError as error:

        raise RuntimeError(
            "kagglehub is required "
            "for GeeksforGeeks "
            "extraction."
        ) from error

    print(
        "Downloading "
        "GeeksforGeeks dataset..."
    )

    dataset_path = Path(
        kagglehub.dataset_download(
            GFG_DATASET_ID
        )
    )

    df = load_gfg_csv(
        dataset_path
    )

    # فلترة الجديد/المتغيّر بالـ URL: نفس منطق Medium، المحتوى
    # جاي مجاني مع الـ dataset فنقدر نقارن بهاش المحتوى.
    known_urls = (
        {}
        if refresh
        else load_known_urls_from_adls(
            "GeeksforGeeks"
        )
    )

    skipped_unchanged = 0

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

        title = str(
            raw.get("title")
            or ""
        )

        tags = raw.get(
            "tags"
        )

        search_text = " ".join(
            [
                title,
                str(tags or ""),
                str(
                    raw.get(
                        "content"
                    )
                    or ""
                )[:5000],
            ]
        )

        category = (
            classify_topic(
                search_text
            )
        )

        if not category:
            continue

        url = raw.get("url")
        content = raw.get("content")

        if (
            known_urls
            and known_urls.get(url)
            == compute_content_hash(
                content
            )
        ):
            skipped_unchanged += 1
            continue

        records.append(
            {
                "source":
                    "GeeksforGeeks",

                "category":
                    category,

                "title":
                    title,

                "author":
                    "",

                "publication_date":
                    "",

                "description":
                    "",

                "url":
                    url,

                "content":
                    content,

                "tags":
                    tags,
            }
        )

    save_json(
        records,
        GFG_OUTPUT,
    )

    print(
        "GeeksforGeeks saved: "
        f"{len(records)} records "
        "(جديد/متغيّر). تخطينا "
        f"{skipped_unchanged} مقالة "
        "معروفة وما تغيرت."
    )

    save_known_urls_to_adls(
        "GeeksforGeeks",
        build_seen_map(
            records,
            url_key="url",
            content_fn=lambda record: (
                record.get("content")
            ),
        ),
    )

    return GFG_OUTPUT


# ============================================================
# RAW FILE LOADING
# ============================================================

def load_raw_file(
    path,
):

    path = Path(path)

    if (
        path.suffix.lower()
        == ".json"
    ):

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return pd.DataFrame(
            data
        )

    if (
        path.suffix.lower()
        == ".csv"
    ):

        return pd.read_csv(
            path
        )

    raise ValueError(
        "Unsupported raw file: "
        f"{path}"
    )


def discover_source_files(
    source,
    raw_dir=RAW_DIR,
):

    if source not in RAW_PATTERNS:

        raise ValueError(
            f"Unsupported source: "
            f"{source}"
        )

    files = []

    for pattern in (
        RAW_PATTERNS[source]
    ):

        files.extend(
            sorted(
                Path(raw_dir).glob(
                    pattern
                )
            )
        )

    if (
        source
        in {
            "dev.to",
            "freeCodeCamp",
        }
        and len(files) > 1
    ):

        files = [
            sorted(files)[-1]
        ]

    return files


def load_source_raw(
    source,
    raw_dir=RAW_DIR,
):

    files = (
        discover_source_files(
            source,
            raw_dir,
        )
    )

    if not files:

        raise FileNotFoundError(
            f"No raw data for "
            f"{source}"
        )

    frames = [
        load_raw_file(
            file
        )
        for file in files
    ]

    return pd.concat(
        frames,
        ignore_index=True,
        sort=False,
    )


def load_all_raw(
    sources=None,
):

    if sources is None:
        sources = (
            SUPPORTED_SOURCES
        )

    return {
        source:
            load_source_raw(
                source
            )
        for source in sources
    }


# ============================================================
# COMPLETE EXTRACTION
# ============================================================

EXTRACTORS = {
    "dev.to":
        extract_devto,

    "Pluralsight":
        extract_pluralsight,

    "freeCodeCamp":
        extract_freecodecamp,

    "Medium":
        extract_medium,

    "GeeksforGeeks":
        extract_geeksforgeeks,
}


class ExtractionTimeout(Exception):
    """Raised when a single source exceeds its time budget."""


def _timeout_handler(signum, frame):
    raise ExtractionTimeout(
        "Extraction step exceeded its "
        "time budget."
    )


# Hard wall-clock ceiling per source, in seconds.
# This protects the whole job from a single source
# hanging (e.g. a slow/blocked network response that
# does not cleanly raise a request-level timeout) by
# forcing a hard interrupt after this many seconds,
# regardless of what the source's code is doing.
SOURCE_TIME_BUDGET_SECONDS = {
    "dev.to": 600,
    "Pluralsight": 1500,
    "freeCodeCamp": 900,
    "Medium": 600,
    "GeeksforGeeks": 300,
}


def run_extraction(
    refresh=False,
    sources=None,
):
    """
    Ensure raw data exists for the given sources
    (all five by default).

    refresh=False:
        Skip URLs already recorded in persistent ADLS known-URL state.

    refresh=True:
        Ignore known-URL state and collect the selected sources again.

    sources:
        Optional list of source names to run (subset of
        SUPPORTED_SOURCES). Defaults to all five when not
        given, so this same function powers both the real
        production run and a manual single-source test run.

    Each source runs under its own hard time budget
    (SOURCE_TIME_BUDGET_SECONDS) and its own
    try/except, so a single source hanging or failing
    cannot take down the other four.
    """

    outputs = {}

    sources_to_run = (
        sources
        if sources
        else SUPPORTED_SOURCES
    )

    for source in (
        sources_to_run
    ):

        print(
            "\n"
            + "=" * 60
        )

        print(
            f"EXTRACTING: {source}"
        )

        print(
            "=" * 60
        )

        budget_seconds = (
            SOURCE_TIME_BUDGET_SECONDS.get(
                source,
                900,
            )
        )

        previous_handler = (
            signal.signal(
                signal.SIGALRM,
                _timeout_handler,
            )
        )

        signal.alarm(budget_seconds)

        try:

            outputs[source] = (
                EXTRACTORS[source](
                    refresh=refresh
                )
            )

        except Exception as error:

            print(
                f"\n{source} extraction "
                f"FAILED or TIMED OUT "
                f"after {budget_seconds}s: "
                f"{error}"
            )

            print(
                f"Continuing with the "
                f"remaining sources."
            )

            outputs[source] = None

        finally:

            signal.alarm(0)

            signal.signal(
                signal.SIGALRM,
                previous_handler,
            )

    return outputs