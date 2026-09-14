## Data Source: freeCodeCamp News

- **Name:** freeCodeCamp News
- **Endpoint / URL:** https://www.freecodecamp.org/news/
- **Access method:** Web Scraping (no public API available) — Playwright
  renders the search pages (`?query=ai`, `?query=cloud`, `?query=data`)
  and handles the JavaScript-based "Load More" pagination; BeautifulSoup
  parses each article's HTML.
- **Rate limits / politeness:** No official rate limit published. A
  1-second delay is added between article requests, and a 2-second wait
  after each "Load More" click.
- **Licence / Terms of Use:** freeCodeCamp content is publicly readable;
  verify the current Terms of Service before final submission. Only
  public article metadata is collected (title, author, date,
  description) — no full article body is stored.
- **Fields collected:** source, category, title, author,
  publication_date, description, url, topic, matched_keywords
- **Note:** Raw scraped data is not committed to the repository (see
  `.gitignore`). It's fully reproducible by running
  `notebooks/01_extract.ipynb`.

## Schema (Task 3)

| Column           | Data Type | Nullable | Allowed Values / Range                                |
| ---------------- | --------- | -------- | ----------------------------------------------------- |
| source           | string    | N        | equals "freeCodeCamp"                                 |
| title            | string    | N        | non-empty                                             |
| url              | string    | N        | starts with "https://"                                |
| publication_date | date      | N        | valid date                                            |
| topic            | string    | N        | one of: AI, Cloud, Data Science                       |
| author           | string    | N        | non-empty (placeholder "No author" counts as present) |
| description      | string    | Y        | —                                                     |
| category         | string    | Y        | —                                                     |
| matched_keywords | string    | Y        | —                                                     |
