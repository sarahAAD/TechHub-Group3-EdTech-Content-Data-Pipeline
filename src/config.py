"""Shared paths and settings for the freeCodeCamp ETL pipeline (Tasks 1-4)."""

from pathlib import Path


# ==============================================================================
# PROJECT PATHS
# ==============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# TASK 1 - FREECODECAMP SOURCE
# ==============================================================================

BASE_SEARCH_URL = "https://www.freecodecamp.org/news/search/?query={}"

SEARCH_TERMS = {
    "AI": "ai",
    "Cloud": "cloud",
    "Data Science": "data",
}

CLICKS_PER_TERM = 10
TARGET_ARTICLES_PER_TERM = 150

REQUEST_DELAY = 1


# ==============================================================================
# KEYWORDS - ENRICHMENT
# ==============================================================================

AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "generative ai",
    "generative artificial intelligence",
    "large language model",
    "large language models",
    "llm",
    "chatgpt",
    "openai",
    "neural network",
    "neural networks",
    "computer vision",
    "natural language processing",
    "nlp",
]

CLOUD_KEYWORDS = [
    "cloud computing",
    "cloud",
    "aws",
    "amazon web services",
    "azure",
    "microsoft azure",
    "google cloud",
    "google cloud platform",
    "gcp",
    "cloud architecture",
    "cloud services",
    "cloud storage",
]

DATA_KEYWORDS = [
    "data science",
    "data analysis",
    "data analytics",
    "data engineering",
    "data engineer",
    "data scientist",
    "data visualization",
    "big data",
    "pandas",
    "numpy",
    "sql",
    "data pipeline",
    "data pipelines",
    "data warehouse",
    "data lake",
    "machine data",
]


# ==============================================================================
# TASK 2 - CLEANING
# ==============================================================================

CLEANED_CSV_PATH = INTERIM_DIR / "cleaned.csv"


# ==============================================================================
# TASK 3 - VALIDATION
# ==============================================================================

VALIDATED_CSV_PATH = INTERIM_DIR / "validated.csv"
REJECTED_CSV_PATH = INTERIM_DIR / "rejected.csv"

VALID_TOPICS = {
    "AI",
    "Cloud",
    "Data Science",
}


# ==============================================================================
# TASK 4 - TRANSFORMATION
# ==============================================================================

FINAL_CSV_PATH = PROCESSED_DIR / "final.csv"
