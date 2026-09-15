"""
Tests for Task 4 transformation rules (R1, R2, R3).

Migrated from the assertion cells in notebooks/04_join_transform.ipynb, as
required at the Integration stage. Run with: pytest tests/test_transform.py
"""

import pandas as pd
from src.transform import count_keywords, classify_length, apply_transformation_rules


# ==========================================
# R1: publish_year
# ==========================================

def test_publish_year_sanity_check():
    # sanity check on the logic itself
    assert pd.to_datetime("2026-09-11").year == 2026


def test_publish_year_within_expected_range():
    df = pd.DataFrame({
        "publication_date": ["2016-01-01", "2026-09-11"],
        "matched_keywords": ["none", "none"],
        "description": ["x", "y"],
    })
    df_final = apply_transformation_rules(df)
    assert df_final["publish_year"].dropna().between(2010, 2030).all(), \
        "Unexpected publish_year values found"


# ==========================================
# R2: keyword_count
# ==========================================

def test_keyword_count_empty_case():
    assert count_keywords("none") == 0, "R2 failed on empty case"


def test_keyword_count_null_case():
    assert count_keywords(None) == 0, "R2 failed on null case"


def test_keyword_count_multi_keyword_case():
    assert count_keywords("ai, llm") == 2, "R2 failed on multi-keyword case"


def test_keyword_count_single_keyword_case():
    assert count_keywords("ai") == 1, "R2 failed on single-keyword case"


def test_keyword_count_never_negative():
    df = pd.DataFrame({
        "publication_date": ["2026-09-11"],
        "matched_keywords": ["ai, llm, chatgpt"],
        "description": ["x"],
    })
    df_final = apply_transformation_rules(df)
    assert (df_final["keyword_count"] >= 0).all(), "Negative keyword_count found"


# ==========================================
# R3: length_category
# ==========================================

def test_length_category_empty_string():
    assert classify_length("") == "short", "R3 failed on empty string"


def test_length_category_null_case():
    assert classify_length(None) == "unknown", "R3 failed on null case"


def test_length_category_short():
    assert classify_length("x" * 50) == "short"


def test_length_category_medium():
    assert classify_length("x" * 150) == "medium"


def test_length_category_long():
    assert classify_length("x" * 250) == "long"


def test_length_category_only_valid_labels():
    df = pd.DataFrame({
        "publication_date": ["2026-09-11", "2026-09-11"],
        "matched_keywords": ["none", "none"],
        "description": ["short one", "x" * 300],
    })
    df_final = apply_transformation_rules(df)
    assert df_final["length_category"].isin(
        ["short", "medium", "long", "unknown"]
    ).all()