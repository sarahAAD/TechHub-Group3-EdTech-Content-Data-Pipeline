"""
Unified extraction layer.

Collects data from:

1. dev.to          -> public API
2. Pluralsight     -> web scraping
3. freeCodeCamp    -> Playwright
4. Medium          -> Hugging Face
5. GeeksforGeeks   -> Kaggle

By default, existing raw files are reused.

Use refresh=True to force a new extraction.
"""

from __future__ import annotations

import ast
import csv
import datetime
import json
import os
import re
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

    existing = (
        discover_source_files(
            "dev.to"
        )
    )

    if existing and not refresh:

        print(
            "dev.to raw file already exists. "
            "Skipping extraction."
        )

        return existing[-1]

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

        if (
            output.exists()
            and not refresh
        ):

            print(
                "Pluralsight "
                f"{category_name} "
                "already exists. "
                "Skipping extraction."
            )

            continue

        article_urls = (
            discover_pluralsight_urls(
                category_config["url"],
                category_config[
                    "max_pages"
                ],
            )
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

    return outputs


# ============================================================
# FREECODECAMP EXTRACTION
# ============================================================

def extract_freecodecamp(
    refresh=False,
):

    existing = (
        discover_source_files(
            "freeCodeCamp"
        )
    )

    if existing and not refresh:

        print(
            "freeCodeCamp raw file "
            "already exists. "
            "Skipping extraction."
        )

        return existing[-1]

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

    with sync_playwright() as p:

        browser = (
            p.chromium.launch(
                headless=True
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

                except Exception as error:

                    print(
                        "freeCodeCamp failed: "
                        f"{url}: {error}"
                    )

                time.sleep(
                    FREECODECAMP_REQUEST_DELAY
                )

        browser.close()

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

    if (
        MEDIUM_OUTPUT.exists()
        and not refresh
    ):

        print(
            "Medium raw file already "
            "exists. Skipping extraction."
        )

        return MEDIUM_OUTPUT

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

    df = dataset.to_pandas()

    records = []

    for raw in df.to_dict(
        orient="records"
    ):

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
                    raw.get("url"),

                "content":
                    raw.get("text"),

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
        f"{len(records)} records"
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

    if (
        GFG_OUTPUT.exists()
        and not refresh
    ):

        print(
            "GeeksforGeeks raw file "
            "already exists. "
            "Skipping extraction."
        )

        return GFG_OUTPUT

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
                    raw.get("url"),

                "content":
                    raw.get(
                        "content"
                    ),

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
        f"{len(records)} records"
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


def run_extraction(
    refresh=False,
):
    """
    Ensure raw data exists for all five sources.

    refresh=False:
        Reuse an existing source file when available.

    refresh=True:
        Force all five sources to be collected again.
    """

    outputs = {}

    for source in (
        SUPPORTED_SOURCES
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

        outputs[source] = (
            EXTRACTORS[source](
                refresh=refresh
            )
        )

    return outputs