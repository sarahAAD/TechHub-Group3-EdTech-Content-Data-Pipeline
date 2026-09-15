"""
Task 1 — Extract: freeCodeCamp

Scrapes AI / Cloud / Data Science articles from freeCodeCamp News using
direct search URLs (?query=ai, ?query=cloud, ?query=data) and saves the
result to data/raw/.

Technical note: Playwright's Sync API cannot run inside an already-running
event loop (e.g. Jupyter's). Running it inside a background Thread gives it
a fresh context that avoids the conflict, on Windows or otherwise.
"""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import time
import re
import datetime
import threading
import asyncio
import sys


# ==========================================
# SETTINGS
# ==========================================

BASE_SEARCH_URL = "https://www.freecodecamp.org/news/search/?query={}"

# One broad search term per topic — trades some recall for speed,
# versus checking all 43 keywords against every article on the full listing.
SEARCH_TERMS = {
    "AI": "ai",
    "Cloud": "cloud",
    "Data Science": "data",
}

CLICKS_PER_TERM = 10
TARGET_ARTICLES_PER_TERM = 150


# ==========================================
# KEYWORDS (for enrichment only)
# Filtering happens via the search URL itself. These lists are only used
# afterwards to fill the matched_keywords column for extra detail.
# ==========================================

AI_KEYWORDS = [
    "artificial intelligence", "machine learning", "deep learning",
    "generative ai", "generative artificial intelligence",
    "large language model", "large language models", "llm",
    "chatgpt", "openai", "neural network", "neural networks",
    "computer vision", "natural language processing", "nlp"
]

CLOUD_KEYWORDS = [
    "cloud computing", "cloud", "aws", "amazon web services",
    "azure", "microsoft azure", "google cloud",
    "google cloud platform", "gcp", "cloud architecture",
    "cloud services", "cloud storage"
]

DATA_KEYWORDS = [
    "data science", "data analysis", "data analytics",
    "data engineering", "data engineer", "data scientist",
    "data visualization", "big data", "pandas", "numpy", "sql",
    "data pipeline", "data pipelines", "data warehouse",
    "data lake", "machine data"
]


def matches_keyword(text, keyword):
    pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"
    return re.search(pattern, text.lower()) is not None


def detect_matched_keywords(title, description, category):
    text = (title + " " + description + " " + category).lower()
    return [kw for kw in AI_KEYWORDS + CLOUD_KEYWORDS + DATA_KEYWORDS
            if matches_keyword(text, kw)]


# ==========================================
# COLLECT ARTICLE LINKS FROM A SEARCH PAGE
# ==========================================

def collect_links(page, search_url, clicks_needed):
    print(f"Opening: {search_url}")
    page.goto(search_url, wait_until="networkidle")

    for i in range(clicks_needed):
        try:
            page.click("#readMoreBtn", timeout=5000)
            print(f"  Clicked 'Load More' ({i + 1}/{clicks_needed})")
            page.wait_for_timeout(2000)
        except Exception:
            print("  No more 'Load More' button — stopping pagination.")
            break

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.find_all("article", class_="post-card")
    print(f"  Found {len(articles)} article cards.\n")

    items = []
    for article in articles:
        link_tag = article.find("a", class_="post-card-image-link")
        if link_tag:
            href = link_tag.get("href")
            link = (href if href.startswith("http") else "https://www.freecodecamp.org" + href) if href else None
        else:
            link = None

        # Author name lives inside a link with class "meta-item"
        author_tag = article.find("a", class_="meta-item")
        author = author_tag.get_text(" ", strip=True) if author_tag else "No author"

        tag_span = article.find("span", class_="post-card-tags")
        category_tag = tag_span.find("a") if tag_span else None
        category = category_tag.get_text(" ", strip=True) if category_tag else "No category"

        title_tag = article.find("h2") or article.find("h3")
        listing_title = title_tag.get_text(" ", strip=True) if title_tag else ""

        description_tag = article.find("p")
        listing_description = description_tag.get_text(" ", strip=True) if description_tag else ""

        if link:
            items.append({
                "url": link, "author": author, "category": category,
                "listing_title": listing_title, "listing_description": listing_description
            })

    return items


# ==========================================
# SCRAPE ONE ARTICLE PAGE FOR FULL DETAILS
# ==========================================

def scrape_article(page, url, listing_author, listing_category, primary_topic):
    page.goto(url, wait_until="networkidle")
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(" ", strip=True) if title_tag else "No title"

    pub_date_tag = soup.find("meta", attrs={"property": "article:published_time"})
    pub_date = pub_date_tag.get("content") if pub_date_tag else "No date"

    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag.get("content") if desc_tag else "No description"

    matched_keywords = detect_matched_keywords(title, description, listing_category)

    return {
        "source": "freeCodeCamp", "category": listing_category, "title": title,
        "author": listing_author, "publication_date": pub_date,
        "description": description, "url": url, "topic": primary_topic,
        "matched_keywords": ", ".join(matched_keywords)
    }


# ==========================================
# MAIN ENTRY POINT — this is what main.py calls
# ==========================================

def scrape_freecodecamp(output_dir="data/raw"):
    """
    Runs the full freeCodeCamp scraper and saves the result as a CSV inside
    output_dir. Returns the path to the saved file.
    """
    results = []
    scraper_error = None

    def run_scraper():
        nonlocal results, scraper_error
        # Playwright launches the browser as a subprocess. On Windows only
        # the Proactor event loop supports subprocesses (Jupyter defaults
        # to Selector) — running this inside its own thread with its own
        # fresh event loop avoids the conflict either way.
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            asyncio.set_event_loop(asyncio.new_event_loop())

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                seen_urls = set()

                for topic, term in SEARCH_TERMS.items():
                    search_url = BASE_SEARCH_URL.format(term)
                    items = collect_links(page, search_url, CLICKS_PER_TERM)

                    collected_for_term = 0
                    for item in items:
                        if collected_for_term >= TARGET_ARTICLES_PER_TERM:
                            break
                        if item["url"] in seen_urls:
                            continue
                        seen_urls.add(item["url"])

                        try:
                            data = scrape_article(page, item["url"], item["author"], item["category"], topic)
                            results.append(data)
                            collected_for_term += 1
                            print(f"  [{topic}] [{collected_for_term}/{TARGET_ARTICLES_PER_TERM}] {data['title']}")
                        except Exception as e:
                            print(f"  [{topic}] Failed: {item['url']} - {e}")

                        time.sleep(1)

                browser.close()
        except Exception as e:
            scraper_error = e

    scraper_thread = threading.Thread(target=run_scraper)
    scraper_thread.start()
    scraper_thread.join()

    if scraper_error:
        raise scraper_error

    print(f"\nDone scraping. {len(results)} total articles collected across {len(SEARCH_TERMS)} search terms.")

    fieldnames = ["source", "category", "title", "author", "publication_date",
                  "description", "url", "topic", "matched_keywords"]

    today = datetime.date.today().isoformat()
    output_file = f"{output_dir}/freecodecamp_{today}.csv"

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Saved {len(results)} articles")
    print(f"File: {output_file}")

    return output_file


# Lets you test this file alone: `python src/extract.py` from the repo root
if __name__ == "__main__":
    scrape_freecodecamp()