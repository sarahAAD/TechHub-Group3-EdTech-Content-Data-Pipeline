# TechHub-Group3-EdTech-Content-Data-Pipeline

An end-to-end incremental ETL pipeline that extracts, profiles, validates, and transforms
article data from the dev.to (Forem) public Articles API into an analysis-ready dataset.

Source: `GET https://dev.to/api/articles` (listing, filterable by `tag`) and
`GET https://dev.to/api/articles/{id}` (single article, full body). The listing endpoint is
public — no API key required; an optional `DEVTO_API_KEY` (read from the environment, never
hardcoded) is only needed for endpoints that act on your own account. dev.to rate-limits
aggressive callers, so requests retry with exponential backoff on `HTTP 429`. Licence / terms
of use: Forem / dev.to Developer API — https://developers.forem.com/api

| Column Name | Data Type | Nullable | Allowed Values / Constraints |
|---|---|---|---|
| `external_id` | String | No | Must match `devto:<digits>` |
| `title` | String | No | Non-empty character string |
| `source` | String | No | Must be exactly `'dev.to'` |
| `author` | String | No | Non-empty text string |
| `published_date` | String (ISO) | No | Valid ISO 8601 timestamp |
| `url` | String | No | Must start with `'https://'` |
| `topic` | String | Yes | Any string, empty allowed |
| `tags` | String | Yes | Comma-separated tag names |
| `description` | String | Yes | Free-text summary block |
| `content_type` | String | No | Must be exactly `'article'` |
| `reading_time_minutes` | Integer | No | >= 0 |
| `reactions_count` | Integer | No | >= 0 |
| `comments_count` | Integer | No | >= 0 |
| `cover_image` | String (URL) | Yes | Starts with `'http'` when present |
| `content_markdown` | String | Yes | Raw article body (Markdown) |
| `content_html` | String | Yes | Raw article body (HTML) |
| `content_clean` | String | Yes | Plain-text body, markup/Liquid noise stripped |

> Setup steps, run instructions, and a data dictionary for the final CSV are added at the
> Integration stage, once Task 4 (join/transform across all members' sources) produces
> `data/processed/final.csv`.
