"""
Configuration for the unified EdTech Content Data Pipeline.
"""

from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

for directory in (
    RAW_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
):
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ============================================================
# UNIFIED SCHEMA
# ============================================================

COMMON_COLUMNS = [
    "source",
    "category",
    "title",
    "author",
    "publication_date",
    "description",
    "url",
    "content",
    "tags",
]

SUPPORTED_SOURCES = [
    "dev.to",
    "Pluralsight",
    "freeCodeCamp",
    "Medium",
    "GeeksforGeeks",
]


# ============================================================
# RAW FILE PATTERNS
# ============================================================

RAW_PATTERNS = {
    "dev.to": [
        "devto_*.json",
    ],

    "Pluralsight": [
        "pluralsight_ai_data_articles.json",
        "pluralsight_cloud_articles.json",
    ],

    "freeCodeCamp": [
        "freecodecamp_*.csv",
    ],

    "Medium": [
        "medium_articles.json",
    ],

    "GeeksforGeeks": [
        "geeksforgeeks_articles.json",
    ],
}


# ============================================================
# DEV.TO
# ============================================================

DEVTO_API_BASE = "https://dev.to/api"

DEVTO_TAGS = [
    "machinelearning",
    "datascience",
    "cloud",
    "aws",
    "ai",
]

DEVTO_MAX_PAGES_PER_TAG = 2
DEVTO_PER_PAGE = 30
DEVTO_CONTENT_DELAY = 0.3


# ============================================================
# PLURALSIGHT
# ============================================================

PLURALSIGHT_BASE_URL = "https://pluralsight.com"

PLURALSIGHT_CATEGORIES = {
    "AI & Data": {
        "url":
            "https://pluralsight.com/resources/blog/ai-and-data",

        "output":
            RAW_DIR / "pluralsight_ai_data_articles.json",

        "max_pages":
            31,
    },

    "Cloud": {
        "url":
            "https://pluralsight.com/resources/blog/cloud",

        "output":
            RAW_DIR / "pluralsight_cloud_articles.json",

        "max_pages":
            47,
    },
}

PLURALSIGHT_MAX_ARTICLES = 300

PLURALSIGHT_REQUEST_DELAY = 2
PLURALSIGHT_REQUEST_TIMEOUT = 30

PLURALSIGHT_HEADERS = {
    "User-Agent":
        "learningProjectPipeline/1.0",

    "Accept-Language":
        "en-US,en;q=0.9",
}


# ============================================================
# FREECODECAMP
# ============================================================

FREECODECAMP_BASE_SEARCH_URL = (
    "https://www.freecodecamp.org/news/search/?query={}"
)

FREECODECAMP_SEARCH_TERMS = {
    "AI": "ai",
    "Cloud": "cloud",
    "Data Science": "data",
}

FREECODECAMP_CLICKS_PER_TERM = 10

FREECODECAMP_TARGET_ARTICLES_PER_TERM = 150

FREECODECAMP_REQUEST_DELAY = 1


# ============================================================
# MEDIUM
# ============================================================

MEDIUM_DATASET_ID = (
    "BEE-spoke-data/medium-articles-en"
)

MEDIUM_OUTPUT = (
    RAW_DIR / "medium_articles.json"
)


# ============================================================
# GEEKSFORGEEKS
# ============================================================

GFG_DATASET_ID = (
    "naidukarthi2193/"
    "geeks-for-geeks-articles-dataset"
)

GFG_OUTPUT = (
    RAW_DIR / "geeksforgeeks_articles.json"
)


# ============================================================
# AI / DATA / CLOUD KEYWORDS
# ============================================================

AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "generative ai",
    "genai",
    "large language model",
    "large language models",
    "llm",
    "llms",
    "natural language processing",
    "nlp",
    "computer vision",
    "neural network",
    "neural networks",
    "tensorflow",
    "pytorch",
    "scikit-learn",
]

DATA_KEYWORDS = [
    "data science",
    "data scientist",
    "data engineering",
    "data engineer",
    "data analytics",
    "data analysis",
    "big data",
    "data pipeline",
    "data pipelines",
    "etl",
    "elt",
    "data warehouse",
    "data warehousing",
    "data lake",
    "data lakes",
    "database",
    "databases",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "spark",
    "apache spark",
    "airflow",
    "apache airflow",
    "dbt",
    "pandas",
    "numpy",
]

CLOUD_KEYWORDS = [
    "cloud computing",
    "cloud architecture",
    "cloud infrastructure",
    "cloud engineering",
    "cloud engineer",
    "aws",
    "amazon web services",
    "azure",
    "microsoft azure",
    "google cloud",
    "google cloud platform",
    "gcp",
    "serverless",
    "kubernetes",
    "docker",
    "cloud native",
]


# ============================================================
# PIPELINE OUTPUTS
# ============================================================

CLEANED_CSV_PATH = (
    INTERIM_DIR / "cleaned.csv"
)

VALIDATED_CSV_PATH = (
    INTERIM_DIR / "validated.csv"
)

REJECTED_CSV_PATH = (
    INTERIM_DIR / "rejected.csv"
)

FINAL_CSV_PATH = (
    PROCESSED_DIR / "final.csv"
)


# ============================================================
# TRANSFORMATION
# ============================================================

LONG_FORM_WORD_THRESHOLD = 500