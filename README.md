# EdTech Content Data Pipeline

An end-to-end data engineering pipeline that collects, profiles, cleans, standardizes, validates, and transforms educational technology content from multiple public data sources into a unified analysis-ready dataset.

The project focuses on educational content related to **Artificial Intelligence, Data, and Cloud Computing**.

## Data Sources

The pipeline integrates content from five sources using different data collection methods:

| Source | Collection Method | Description |
| :--- | :--- | :--- |
| **dev.to** | Public API | Technical articles collected using the dev.to API |
| **Pluralsight** | Web Scraping | AI & Data and Cloud articles collected from the Pluralsight Blog |
| **freeCodeCamp** | Web Scraping with Playwright | Educational articles discovered through freeCodeCamp search pages and article pages |
| **Medium** | Hugging Face Dataset | Medium articles collected from the `BEE-spoke-data/medium-articles-en` dataset |
| **GeeksforGeeks** | Kaggle Dataset | Technical articles collected from the GeeksforGeeks articles dataset |

The extraction methods are intentionally source-specific because each source exposes its data differently. After extraction, all sources pass through the same standardized processing pipeline.

---

## Pipeline Architecture

The pipeline follows the following flow:

```text
Data Sources
    │
    ├── dev.to API
    ├── Pluralsight Web Scraping
    ├── freeCodeCamp Web Scraping
    ├── Medium Hugging Face Dataset
    └── GeeksforGeeks Kaggle Dataset
    │
    ▼
Data Extraction
    │
    ▼
data/raw/
    │
    ▼
Data Profiling
    │
    ▼
Cleaning & Standardization
    │
    ▼
data/interim/cleaned.csv
    │
    ▼
Schema Validation
    │
    ├── Valid Records
    │       └── data/interim/validated.csv
    │
    └── Rejected Records
            └── data/interim/rejected.csv
    │
    ▼
Transformation & Enrichment
    │
    ▼
data/processed/final.csv
```

---

## Pipeline Stages

### 1. Data Extraction

`src/extract.py` handles source-specific data collection.

The extraction methods include:

- REST API requests for dev.to
- HTTP requests and BeautifulSoup for Pluralsight
- Playwright and BeautifulSoup for freeCodeCamp
- Hugging Face `datasets` for Medium
- `kagglehub` for GeeksforGeeks

Raw files are stored under:

```text
data/raw/
```

The pipeline uses an **incremental/reuse approach** by default. If a raw dataset already exists, it is reused instead of being downloaded or scraped again.

Running:

```bash
python main.py
```

uses existing raw files and extracts only missing sources.

To force all sources to be collected again:

```bash
python main.py --refresh
```

---

### 2. Data Profiling

Each raw dataset is profiled before cleaning.

The profiling stage reports information such as:

- Data types
- Null counts
- Percentage of missing values
- Unique values
- Example values
- Duplicate URLs
- Missing important fields

This allows source-specific data quality issues to be identified before integration.

---

### 3. Cleaning and Standardization

Because each source has a different original schema, source-specific normalization functions convert the datasets into one common structure.

The cleaning stage also performs operations such as:

- Normalizing text fields
- Standardizing publication dates
- Normalizing tags
- Mapping source-specific fields
- Removing records without titles or URLs
- Removing duplicate URLs
- Combining all sources into one dataset

The resulting dataset is stored in:

```text
data/interim/cleaned.csv
```

---

### 4. Schema Validation

After standardization, records are validated against the unified schema and data-quality rules.

Valid records are stored in:

```text
data/interim/validated.csv
```

Rejected records are stored separately in:

```text
data/interim/rejected.csv
```

Rejected records include a `rejection_reason` so that data-quality failures remain traceable.

---

### 5. Transformation and Enrichment

Validated records are enriched with additional analytical fields.

The transformation stage adds:

- `word_count` — number of words in the article content
- `publish_year` — year extracted from the publication date
- `is_long_form` — identifies articles containing more than 500 words
- Missing authors are standardized to `Unknown`

The final analysis-ready dataset is stored in:

```text
data/processed/final.csv
```

---

## Unified Data Schema

All five sources are normalized into the following common schema:

| Column Name | Data Type | Nullable | Description / Constraint |
| :--- | :--- | :--- | :--- |
| **source** | String | No | One of: `dev.to`, `Pluralsight`, `freeCodeCamp`, `Medium`, `GeeksforGeeks` |
| **category** | String | Yes | Topic/category associated with the article |
| **title** | String | No | Non-empty article title |
| **author** | String | Yes | Article author; missing values are later standardized to `Unknown` |
| **publication_date** | String (ISO) | Yes | Normalized publication date when available |
| **description** | String | Yes | Article summary or description when available |
| **url** | String | No | Valid HTTP/HTTPS article URL |
| **content** | String | No* | Full article text |
| **tags** | String | Yes | Normalized comma-separated keywords/tags |

> `author` and `publication_date` may be unavailable for some dataset sources such as GeeksforGeeks and are therefore allowed to be missing during validation.

The final transformed dataset additionally contains:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| **word_count** | Integer | Number of words in the article content |
| **publish_year** | Integer / Null | Publication year derived from `publication_date` |
| **is_long_form** | Boolean | `True` when the article contains more than 500 words |

---

## Project Structure

```text
TechHub-Group3/
│
├── data/
│   ├── raw/
│   │   └── .gitkeep
│   │
│   ├── interim/
│   │   └── .gitkeep
│   │
│   └── processed/
│       └── .gitkeep
│
├── notebooks/
│   └── source exploration and ingestion notebooks
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── extract.py
│   ├── profile.py
│   ├── clean.py
│   ├── schema.py
│   └── transform.py
│
├── tests/
│   ├── test_extract.py
│   ├── test_clean.py
│   ├── test_schema.py
│   └── test_transform.py
│
├── main.py
├── requirements.txt
├── .gitignore
└── README.md
```

Generated datasets under `data/raw`, `data/interim`, and `data/processed` are not committed to Git. They can be reproduced by running the pipeline.

---

# Setup

## 1. Clone the Repository

```bash
git clone https://github.com/sarahAAD/TechHub-Group3-EdTech-Content-Data-Pipeline
cd TechHub-Group3
```

---

## 2. Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the terminal should display:

```text
(.venv)
```

---

## 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

The project uses packages including:

- pandas
- requests
- beautifulsoup4
- datasets
- kagglehub
- playwright
- pytest

---

## 4. Install the Playwright Browser

freeCodeCamp extraction uses Playwright and requires Chromium.

Run:

```powershell
playwright install chromium
```

The Chromium installation is managed by Playwright and does not need to be committed to Git.

---

## 5. Run the Tests

Before running the complete pipeline:

```powershell
python -m pytest -v
```

The tests cover:

- Raw JSON/CSV loading
- Source file discovery
- Topic classification
- Source-specific normalization
- Cross-source duplicate handling
- Schema validation
- Rejected record handling
- Data transformations
- Final output column selection

---

## 6. Run the Pipeline

Run:

```powershell
python main.py
```

By default, the pipeline checks `data/raw/` first.

If a source already has raw data, that source is reused. If its raw data is missing, the corresponding extraction process is executed.

For example:

```text
Pluralsight raw data exists
    → reuse

Medium raw data exists
    → reuse

GeeksforGeeks raw data exists
    → reuse

dev.to raw data missing
    → call dev.to API

freeCodeCamp raw data missing
    → run Playwright extraction
```

---

## Force a Full Refresh

To ignore existing raw files and recollect all sources:

```powershell
python main.py --refresh
```

This can take considerably longer because datasets may need to be downloaded again and web sources scraped again.

---

## Expected Output

After a successful run:

```text
data/
├── raw/
│   ├── devto_<date>.json
│   ├── freecodecamp_<date>.csv
│   ├── pluralsight_ai_data_articles.json
│   ├── pluralsight_cloud_articles.json
│   ├── medium_articles.json
│   └── geeksforgeeks_articles.json
│
├── interim/
│   ├── cleaned.csv
│   ├── validated.csv
│   └── rejected.csv
│
└── processed/
    └── final.csv
```

---

## Data Quality Considerations

The five sources contain different levels of metadata completeness.

For example:

- Some GeeksforGeeks records do not provide author or publication date information.
- Source-specific categories and tags differ and must be normalized.
- Duplicate URLs can occur during multi-source integration.
- Web sources may change their HTML structure over time.
- API rate limits and network errors may affect extraction.
- Dataset sources can be significantly larger than scraped sources.

The pipeline preserves missing source information rather than inventing unavailable metadata.

---

## Testing

The project uses `pytest` for automated testing.

Run:

```powershell
python -m pytest -v
```

The test suite verifies the shared extraction utilities, cleaning logic, source normalization, schema validation, rejection handling, and transformations without requiring live web requests during unit testing.