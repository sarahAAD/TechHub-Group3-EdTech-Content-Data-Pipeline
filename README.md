# TechHub — EdTech Content Data Pipeline

Pipeline that collects, cleans, validates, and transforms educational
articles about AI, Cloud, and Data Science from multiple public sources
into one analysis-ready dataset.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

## Data Source: freeCodeCamp News

- **Name:** freeCodeCamp News
- **Endpoint / URL:** https://www.freecodecamp.org/news/
- **Access method:** Web Scraping (no public API available) — Playwright
  renders the search pages (`?query=ai`, `?query=cloud`, `?query=data`)
  and handles the JavaScript-based "Load More" pagination; BeautifulSoup
  parses each article's HTML.
- **Rate limits / politeness:** No official rate limit published. A
  1-second delay is added between article requests, and a 2-second wait
  after each "Load More" click.
- **Licence / Terms of Use:** freeCodeCamp content is publicly readable;
  verify the current Terms of Service before final submission. Only
  public article metadata is collected (title, author, date,
  description) — no full article body is stored.
- **Fields collected:** source, category, title, author,
  publication_date, description, url, topic, matched_keywords
- **Note:** Raw scraped data is not committed to the repository (see
  `.gitignore`). It's fully reproducible by running
  `notebooks/01_extract.ipynb`.

## Schema (Task 3)

| Column           | Data Type | Nullable | Allowed Values / Range                                |
| ---------------- | --------- | -------- | ----------------------------------------------------- |
| source           | string    | N        | equals "freeCodeCamp"                                 |
| title            | string    | N        | non-empty                                             |
| url              | string    | N        | starts with "https://"                                |
| publication_date | date      | N        | valid date                                            |
| topic            | string    | N        | one of: AI, Cloud, Data Science                       |
| author           | string    | N        | non-empty (placeholder "No author" counts as present) |
| description      | string    | Y        | —                                                     |
| category         | string    | Y        | —                                                     |
| matched_keywords | string    | Y        | —                                                     |

## Join Specification (Task 4)

- **Current state:** single source (freeCodeCamp), so no join between two
  tables is performed at this stage.
- **Planned join (once merged with teammates' sources):**
  - **Keys:** `url` (each article's URL is unique across all sources)
  - **Join type:** not a traditional join — sources are _stacked_
    (concatenated) into one table, since each source contributes distinct
    rows rather than matching columns
  - **Expected row count:** sum of each source's validated row count
    (no overlap expected)
  - **Duplicate handling:** deduplicate on `url` after concatenation, in
    case the same article is cross-posted on two sites

## Transformation Rules (Task 4)

| Rule ID | Description                                                       | Input Column(s)  | Output Column   |
| ------- | ----------------------------------------------------------------- | ---------------- | --------------- |
| R1      | Extract the publication year from the date                        | publication_date | publish_year    |
| R2      | Count how many keywords matched                                   | matched_keywords | keyword_count   |
| R3      | Classify article length (short/medium/long) by description length | description      | length_category |

## Pipeline Stages

| Stage                 | Notebook                   | Input           | Output                          |
| --------------------- | -------------------------- | --------------- | ------------------------------- |
| 1 — Extract           | `01_extract.ipynb`         | Source websites | `data/raw/*.csv`                |
| 2 — Profile & Clean   | `02_profile_clean.ipynb`   | `data/raw/`     | `data/interim/cleaned.csv`      |
| 3 — Schema & Validate | `03_schema_validate.ipynb` | `cleaned.csv`   | `validated.csv`, `rejected.csv` |
| 4 — Join & Transform  | `04_join_transform.ipynb`  | `validated.csv` | `data/processed/final.csv`      |
