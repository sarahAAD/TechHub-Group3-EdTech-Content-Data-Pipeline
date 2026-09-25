import math
import os
import hashlib

from dotenv import load_dotenv
from databricks import sql
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()

app = FastAPI(title="TechHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Databricks configuration
# ============================================================

DATABRICKS_SERVER_HOSTNAME = os.getenv("DATABRICKS_SERVER_HOSTNAME")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

GOLD_PATH = (
    "abfss://edtech@edtechpipline26.dfs.core.windows.net/"
    "processed/final/"
)


def get_connection():
    return sql.connect(
        server_hostname=DATABRICKS_SERVER_HOSTNAME,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN,
    )


def rows_to_dicts(cursor, rows):
    columns = [column[0] for column in cursor.description]

    return [
        dict(zip(columns, row))
        for row in rows
    ]


# ============================================================
# Health check
# ============================================================

@app.get("/")
def root():
    return {
        "message": "TechHub API is running",
        "data_source": "Databricks Gold Delta"
    }


# ============================================================
# Paginated article list
# ============================================================

@app.get("/articles")
def get_articles(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        offset = (page - 1) * limit

        with get_connection() as connection:
            with connection.cursor() as cursor:

                # Get total number of articles
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM delta.`{GOLD_PATH}`
                    """
                )

                total = cursor.fetchone()[0]

                # Get only the requested page.
                # Full article content is intentionally excluded.
                cursor.execute(
                    f"""
                    SELECT
                        sha2(url, 256) AS article_id,
                        source,
                        category,
                        title,
                        author,
                        publication_date,
                        description,
                        url,
                        tags,
                        word_count,
                        publish_year,
                        is_long_form
                    FROM delta.`{GOLD_PATH}`
                    ORDER BY
                        publication_date DESC NULLS LAST,
                        title ASC
                    LIMIT {limit}
                    OFFSET {offset}
                    """
                )

                articles = rows_to_dicts(
                    cursor,
                    cursor.fetchall()
                )

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": math.ceil(total / limit),
            "articles": articles,
        }

    except Exception as e:
        print(f"Databricks error: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Could not load articles: {str(e)}"
        )


# ============================================================
# Full individual article
# ============================================================

@app.get("/articles/{article_id}")
def get_article(article_id: str):

    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    f"""
                    SELECT
                        sha2(url, 256) AS article_id,
                        source,
                        category,
                        title,
                        author,
                        publication_date,
                        description,
                        url,
                        content,
                        tags,
                        word_count,
                        publish_year,
                        is_long_form
                    FROM delta.`{GOLD_PATH}`
                    WHERE sha2(url, 256) = ?
                    LIMIT 1
                    """,
                    [article_id]
                )

                row = cursor.fetchone()

                if row is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Article not found"
                    )

                article = rows_to_dicts(
                    cursor,
                    [row]
                )[0]

                return article

    except HTTPException:
        raise

    except Exception as e:
        print(f"Databricks error: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Could not load article: {str(e)}"
        )