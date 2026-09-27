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
# Paginated article list (with server-side search / filters)
# ============================================================

LIST_COLUMNS = """
    article_id,
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
"""

SEARCH_TEXT = """
    lower(concat_ws(' ',
        coalesce(title, ''),
        coalesce(CAST(author AS STRING), ''),
        coalesce(description, ''),
        coalesce(CAST(tags AS STRING), ''),
        coalesce(source, ''),
        coalesce(category, '')
    ))
"""


def build_filters(q, category, source):
    """Return (WHERE clause, params) applied to the WHOLE Gold table."""
    conditions = []
    params = []

    if category:
        conditions.append("lower(trim(category)) = ?")
        params.append(category.strip().lower())

    if source:
        conditions.append("lower(trim(source)) = ?")
        params.append(source.strip().lower())

    if q:
        # Every word must appear somewhere in the searchable fields
        for word in q.lower().split()[:10]:
            conditions.append(f"instr({SEARCH_TEXT}, ?) > 0")
            params.append(word)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


@app.get("/articles")
def get_articles(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=50),
    source: str | None = Query(default=None, max_length=50),
    sort: str = Query(default="mixed", pattern="^(mixed|newest)$"),
):
    """
    sort=mixed  -> round-robin across sources (newest of each source first),
                   so one source (e.g. today's dev.to pull) can't fill a page.
    sort=newest -> strictly by publication date.
    """
    try:
        offset = (page - 1) * limit
        where, params = build_filters(q, category, source)

        if sort == "newest":
            order_by = "publication_date DESC NULLS LAST, title ASC"
        else:
            order_by = (
                "source_rank ASC, publication_date DESC NULLS LAST, "
                "source ASC, title ASC"
            )

        with get_connection() as connection:
            with connection.cursor() as cursor:

                # Total matching articles (whole table, not one page)
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM delta.`{GOLD_PATH}`
                    {where}
                    """,
                    params,
                )

                total = cursor.fetchone()[0]

                # Requested page. Full article content is intentionally excluded.
                cursor.execute(
                    f"""
                    WITH filtered AS (
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
                            is_long_form,
                            ROW_NUMBER() OVER (
                                PARTITION BY lower(trim(source))
                                ORDER BY publication_date DESC NULLS LAST,
                                         title ASC
                            ) AS source_rank
                        FROM delta.`{GOLD_PATH}`
                        {where}
                    )
                    SELECT {LIST_COLUMNS}
                    FROM filtered
                    ORDER BY {order_by}
                    LIMIT {limit}
                    OFFSET {offset}
                    """,
                    params,
                )

                articles = rows_to_dicts(
                    cursor,
                    cursor.fetchall()
                )

        return {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": max(1, math.ceil(total / limit)),
            "query": q,
            "category": category,
            "source": source,
            "sort": sort,
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