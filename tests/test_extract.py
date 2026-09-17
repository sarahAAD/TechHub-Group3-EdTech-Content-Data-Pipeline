import json

import pandas as pd

from src.extract import (
    classify_topic,
    detect_matched_keywords,
    discover_source_files,
    extract_devto,
    extract_geeksforgeeks,
    extract_medium,
    load_raw_file,
    matches_keyword,
)


def test_matches_keyword():

    assert matches_keyword(
        "Introduction to machine learning",
        "machine learning",
    )

    assert not matches_keyword(
        "available",
        "ai",
    )


def test_classify_ai():

    assert (
        classify_topic(
            "Machine learning tutorial"
        )
        == "AI"
    )


def test_classify_data():

    assert (
        classify_topic(
            "Building a data pipeline "
            "with Airflow"
        )
        == "Data"
    )


def test_classify_cloud():

    assert (
        classify_topic(
            "Deploying applications "
            "with AWS"
        )
        == "Cloud"
    )


def test_unrelated_topic():

    assert (
        classify_topic(
            "CSS flexbox tutorial"
        )
        is None
    )


def test_detect_keywords():

    result = (
        detect_matched_keywords(
            "AWS cloud computing "
            "with Docker"
        )
    )

    assert "aws" in result

    assert (
        "cloud computing"
        in result
    )

    assert "docker" in result


def test_load_json_file(
    tmp_path,
):

    path = (
        tmp_path
        / "sample.json"
    )

    path.write_text(
        json.dumps(
            [
                {
                    "title":
                        "AI Article"
                }
            ]
        ),
        encoding="utf-8",
    )

    df = load_raw_file(
        path
    )

    assert len(df) == 1

    assert (
        df.iloc[0]["title"]
        == "AI Article"
    )


def test_load_csv_file(
    tmp_path,
):

    path = (
        tmp_path
        / "sample.csv"
    )

    pd.DataFrame(
        [
            {
                "title":
                    "Cloud Article"
            }
        ]
    ).to_csv(
        path,
        index=False,
    )

    df = load_raw_file(
        path
    )

    assert len(df) == 1


def test_discover_medium(
    tmp_path,
):

    path = (
        tmp_path
        / "medium_articles.json"
    )

    path.write_text(
        "[]",
        encoding="utf-8",
    )

    files = (
        discover_source_files(
            "Medium",
            tmp_path,
        )
    )

    assert len(files) == 1

    assert (
        files[0].name
        == "medium_articles.json"
    )


def test_discover_pluralsight(
    tmp_path,
):

    first = (
        tmp_path
        / (
            "pluralsight_"
            "ai_data_articles.json"
        )
    )

    second = (
        tmp_path
        / (
            "pluralsight_"
            "cloud_articles.json"
        )
    )

    first.write_text(
        "[]",
        encoding="utf-8",
    )

    second.write_text(
        "[]",
        encoding="utf-8",
    )

    files = (
        discover_source_files(
            "Pluralsight",
            tmp_path,
        )
    )

    assert len(files) == 2