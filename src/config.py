from pathlib import Path


# ==============================================================================
# PROJECT PATHS
# ==============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"


# ==============================================================================
# CREATE REQUIRED DIRECTORIES
# ==============================================================================

RAW_DIR.mkdir(parents=True, exist_ok=True)
INTERIM_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# PLURALSIGHT SOURCES
# ==============================================================================

BASE_URL = "https://pluralsight.com"

CATEGORIES = {
    "AI & Data": {
        "url": "https://pluralsight.com/resources/blog/ai-and-data",
        "output": RAW_DIR / "pluralsight_ai_data_articles.json",
        "max_pages": 31,
    },
    "Cloud": {
        "url": "https://pluralsight.com/resources/blog/cloud",
        "output": RAW_DIR / "pluralsight_cloud_articles.json",
        "max_pages": 47,
    },
}


# ==============================================================================
# EXTRACTION SETTINGS
# ==============================================================================

MAX_ARTICLES = 10

REQUEST_DELAY = 2

REQUEST_TIMEOUT = 30

USER_AGENT = "learningProjectPipeline/1.0"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9",
}


# ==============================================================================
# TASK 2 - CLEANING
# ==============================================================================

CLEANED_CSV_PATH = INTERIM_DIR / "cleaned.csv"


# ==============================================================================
# TASK 3 - VALIDATION
# ==============================================================================

VALIDATED_CSV_PATH = INTERIM_DIR / "validated.csv"

REJECTED_CSV_PATH = INTERIM_DIR / "rejected.csv"


# ==============================================================================
# TASK 4 - TRANSFORMATION
# ==============================================================================

FINAL_CSV_PATH = PROCESSED_DIR / "final.csv"