# Integration (Combined Dataset)

Combines each teammate's finished, per-source `data/processed/final*.csv`
into one dataset. This is a **stack/concatenation** (`pd.concat`), not a
relational join — there is no shared key across unrelated content
platforms. `url` is used as a dedup safety net across sources (0
duplicates found).

No teammate's original files are modified by this script.

## Sources included

| Contributor | Platform    | Rows |
|---|---|---|
| Batool | dev.to | 275 |
| Sarah | Pluralsight | 20 |
| Sarah | GeeksforGeeks (Kaggle dataset) | 2,454 |
| Sarah | Medium (Hugging Face dataset) | 17,373 |
| Dana | freeCodeCamp | 450 |
| **Total** | | **20,572** |

Sarah's GeeksforGeeks/Medium rows went through the full Task 2-4
pipeline in her `src/` (`clean.py` -> `schema.py` -> `transform.py`,
reused directly, same rules as Pluralsight). `src/schema.py` was
originally hardcoded to Pluralsight only (`source == "Pluralsight"`,
fixed category values, a required `scraped_at` field the new sources
don't have); it has since been generalized to a per-source
`SOURCE_ALLOWED_CATEGORIES` / `SOURCES_REQUIRING_SCRAPED_AT` lookup so
all three sources validate correctly (0 rows rejected for any of them).

## Common schema mapping

| Common name | Batool's column | Sarah's column | Dana's column |
|---|---|---|---|
| published_date | published_date | publication_date | publication_date |
| category | topic | category | topic (AI / Cloud / Data Science) |
| tags | tags | tags | category (site's own page tag) |
| content | content_clean | content | *(not collected)* |

## How to re-run

```
python3 data/integration/combine.py
```
