"""Shared paths and settings for the dev.to ETL pipeline (Tasks 1-4)."""

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
# TASK 1 - DEV.TO (FOREM) PUBLIC ARTICLES API
# ==============================================================================

DEVTO_API_BASE = "https://dev.to/api"

TAGS = ["machinelearning", "datascience", "cloud", "aws", "ai"]

MAX_PAGES_PER_TAG = 2
PER_PAGE = 30

# Seconds between per-article body_markdown/body_html fetches -- be polite to the API.
CONTENT_DELAY = 0.3


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

# Same threshold used for the Pluralsight source, so the two datasets' is_long_form
# columns line up when they're combined at the project-wide integration stage.
LONG_FORM_WORD_THRESHOLD = 500
