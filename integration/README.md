# Integration (Combined Dataset)

Combines each teammate's finished, per-source `data/processed/final.csv`
into one dataset. This is a **stack/concatenation** (`pd.concat`), not a
relational join — there is no shared key across unrelated content
platforms (dev.to, Pluralsight, freeCodeCamp). `url` is used as a
dedup safety net across sources (0 duplicates found).

No teammate's original files are modified by this script. It only reads
each person's existing `final.csv` and writes a new file here,
`final_combined.csv`.

## Sources included

| Contributor | Platform    | Rows |
|---|---|---|
| Batool | dev.to | 275 |
| Sarah | Pluralsight | 20 |
| Dana | freeCodeCamp | 450 |
| **Total** | | **745** |

## Common schema mapping

Column names were aligned across sources (rename only, done in-memory,
originals untouched):

| Common name | Batool's column | Sarah's column | Dana's column |
|---|---|---|---|
| published_date | published_date | publication_date | publication_date |
| category | topic | category | topic (AI / Cloud / Data Science) |
| tags | tags | tags | category (site's own page tag, e.g. "#shadcn ui") |
| content | content_clean | content | *(not collected by this source)* |

All other columns are kept as-is; a column that only exists for one
source is left blank (NaN) for the others after concatenation. A
`contributor` column was added to every row to record which person's
pipeline produced it.

## How to re-run

```
python3 integration/combine.py
```

Reads `data/processed/final.csv` from this repo (Batool) and from the
connected Sarah/Dana folders, writes `integration/final_combined.csv`.
