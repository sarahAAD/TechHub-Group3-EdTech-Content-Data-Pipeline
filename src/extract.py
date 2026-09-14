import json
import os
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    BASE_URL,
    CATEGORIES,
    HEADERS,
    MAX_ARTICLES,
    REQUEST_DELAY,
    REQUEST_TIMEOUT,
)


# --------------------------------------------------
# HTTP SESSION
# --------------------------------------------------

session = requests.Session()
session.headers.update(HEADERS)


# --------------------------------------------------
# FETCH PAGE
# --------------------------------------------------

def fetch_page(url):
    """
    Download a webpage and return its HTML.

    Handles:
    - Successful requests
    - HTTP 429 rate limiting
    - Request exceptions
    """

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT
        )

        print(f"GET {url} -> {response.status_code}")

        if response.status_code == 200:
            time.sleep(REQUEST_DELAY)
            return response.text

        elif response.status_code == 429:
            print("Rate limited. Waiting 10 seconds...")
            time.sleep(10)
            return None

        else:
            print(
                f"Request failed with status code "
                f"{response.status_code}"
            )
            return None

    except requests.RequestException as error:
        print(f"Request error: {error}")
        return None


# --------------------------------------------------
# NORMALIZE URL
# --------------------------------------------------

def normalize_url(url):
    """
    Remove query parameters and fragments from URLs.
    """

    parsed = urlparse(url)

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path.rstrip('/')}"
    )


# --------------------------------------------------
# EXTRACT ARTICLE LINKS
# --------------------------------------------------

def extract_article_links(html, category_url):
    """
    Extract article URLs belonging to the selected
    Pluralsight category.
    """

    soup = BeautifulSoup(html, "html.parser")

    links = set()

    category_path = (
        urlparse(category_url).path.rstrip("/") + "/"
    )

    for anchor in soup.find_all("a", href=True):

        url = urljoin(
            BASE_URL,
            anchor["href"]
        )

        url = normalize_url(url)

        parsed_path = urlparse(url).path

        if parsed_path.startswith(category_path):
            links.add(url)

    return links


# --------------------------------------------------
# DISCOVER ARTICLE URLS
# --------------------------------------------------

def discover_article_urls(
    category_url,
    max_pages,
    max_articles
):
    """
    Scan category pages until enough article URLs
    have been discovered.
    """

    article_urls = set()

    for page in range(1, max_pages + 1):

        # Stop as soon as we have enough URLs
        if len(article_urls) >= max_articles:
            break

        if page == 1:
            page_url = category_url
        else:
            page_url = f"{category_url}?page={page}"

        print(f"Scanning list page {page}...")

        html = fetch_page(page_url)

        if not html:
            continue

        links = extract_article_links(
            html,
            category_url
        )

        article_urls.update(links)

    # IMPORTANT:
    # Return only the requested number of URLs
    return sorted(article_urls)[:max_articles]


# --------------------------------------------------
# EXTRACT ARTICLE
# --------------------------------------------------

def extract_article(url, html, category):
    """
    Parse an individual Pluralsight article.
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # --------------------------------------------------
    # REMOVE UNWANTED ELEMENTS
    # --------------------------------------------------

    toc = soup.find(
        "div",
        class_="table-of-contents"
    )

    if toc:
        toc.decompose()

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

    # --------------------------------------------------
    # TITLE
    # --------------------------------------------------

    title = ""

    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(
            " ",
            strip=True
        )

    # --------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------

    description = ""

    meta_description = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta_description:
        description = meta_description.get(
            "content",
            ""
        ).strip()

    # --------------------------------------------------
    # TAGS
    # --------------------------------------------------

    tags = []

    tag_list = soup.find(
        "ul",
        class_="tag-list-listing"
    )

    if tag_list:

        tags = [
            li.get_text(
                " ",
                strip=True
            )
            for li in tag_list.find_all("li")
            if li.get_text(strip=True)
        ]

    # --------------------------------------------------
    # AUTHOR
    # --------------------------------------------------

    author = ""

    meta_author = soup.find(
        "meta",
        attrs={"name": "author"}
    )

    if meta_author:

        author = meta_author.get(
            "content",
            ""
        ).strip()

    if not author:

        for element in soup.find_all(
            ["p", "div", "span"]
        ):

            text = element.get_text(
                " ",
                strip=True
            )

            if (
                text.startswith("By ")
                and len(text) < 100
            ):
                author = text[3:].strip()
                break

    # --------------------------------------------------
    # PUBLICATION DATE
    # --------------------------------------------------

    publication_date = ""

    date_element = soup.find(
        "p",
        class_="date-length-text"
    )

    if date_element:

        text = date_element.get_text(
            " ",
            strip=True
        )

        publication_date = (
            text.split("•")[0].strip()
        )

    # --------------------------------------------------
    # ARTICLE CONTENT
    # --------------------------------------------------

    content_parts = []

    content_area = (
        soup.find("article")
        or soup.find("main")
        or soup.body
    )

    if content_area:

        for element in content_area.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "p",
                "li",
            ]
        ):

            text = element.get_text(
                " ",
                strip=True
            )

            if not text:
                continue

            # Skip unwanted content
            if text.startswith("By "):
                continue

            if "Minute Read" in text:
                continue

            if "Read article" in text:
                continue

            if "Table of Contents" in text:
                continue

            if "Copyright ©" in text:
                continue

            if "Terms of Use" in text:
                continue

            if "Privacy Policy" in text:
                continue

            # Skip tag-list items
            if element.name == "li":

                parent_classes = " ".join(
                    element.parent.get(
                        "class",
                        []
                    )
                ).lower()

                if "tag-list-listing" in parent_classes:
                    continue

            # Skip promotional content
            if "Advance your tech skills today" in text:
                continue

            if "is a seasoned" in text:
                continue

            if "Subscribe to the newsletter" in text:
                continue

            if "Free individual trial" in text:
                continue

            # Store content
            if element.name in [
                "h1",
                "h2",
                "h3",
                "h4",
            ]:
                content_parts.append(
                    f"\n{text}\n"
                )

            elif element.name == "li":
                content_parts.append(
                    f"- {text}"
                )

            else:
                content_parts.append(text)

    content = "\n\n".join(
        content_parts
    ).strip()

    # --------------------------------------------------
    # RETURN STANDARDIZED RECORD
    # --------------------------------------------------

    return {
        "source": "Pluralsight",
        "category": category,
        "title": title,
        "author": author,
        "publication_date": publication_date,
        "description": description,
        "tags": tags,
        "url": url,
        "content": content,
        "scraped_at": datetime.now().isoformat(),
    }


# --------------------------------------------------
# LOAD EXISTING RESULTS
# --------------------------------------------------

def load_existing_results(output_file):

    if os.path.exists(output_file):

        try:

            with open(
                output_file,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except json.JSONDecodeError:

            return []

    return []


# --------------------------------------------------
# SAVE RESULTS
# --------------------------------------------------

def save_results(results, output_file):

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2
        )


# --------------------------------------------------
# SCRAPE CATEGORY
# --------------------------------------------------

def scrape_category(
    category_name,
    category_config
):
    """
    Scrape one Pluralsight category.
    """

    output_file = category_config["output"]

    print("=" * 60)
    print(
        f"SCRAPING CATEGORY: {category_name}"
    )
    print("=" * 60)

    existing_results = load_existing_results(
        output_file
    )

    existing_urls = {
        item["url"]
        for item in existing_results
        if item.get("url")
    }

    print(
        f"Existing stored records: "
        f"{len(existing_results)}"
    )

    article_urls = discover_article_urls(
        category_config["url"],
        category_config["max_pages"],
        MAX_ARTICLES
    )

    print(
        f"URLs selected for processing: "
        f"{len(article_urls)}"
    )

    results = existing_results.copy()

    for i, url in enumerate(
        article_urls,
        start=1
    ):

        if url in existing_urls:

            print(
                f"[{i}/{len(article_urls)}] "
                f"Already saved, skipping."
            )

            continue

        print(
            f"[{i}/{len(article_urls)}] "
            f"Scraping: {url}"
        )

        html = fetch_page(url)

        if not html:
            continue

        record = extract_article(
            url,
            html,
            category_name
        )

        if record and record["content"]:

            results.append(record)

            save_results(
                results,
                output_file
            )

            print(
                f"Saved: {record['title']}"
            )

        else:

            print(
                "Warning: Article content "
                "parsing was empty. Not saving."
            )

    print(
        f"Total entries saved for "
        f"{category_name}: {len(results)}\n"
    )

    return results


# --------------------------------------------------
# RUN EXTRACTION
# --------------------------------------------------

def run_extraction():

    all_results = {}

    for (
        category_name,
        category_config
    ) in CATEGORIES.items():

        results = scrape_category(
            category_name,
            category_config
        )

        all_results[
            category_name
        ] = results

    return all_results