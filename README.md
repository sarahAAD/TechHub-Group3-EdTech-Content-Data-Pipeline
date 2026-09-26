# TechHub — EdTech Content Data Pipeline

TechHub is an end-to-end Data Engineering project that collects educational technology content from multiple public sources, processes and validates the data through an Azure-based pipeline, and makes the curated content available through a deployed web application.

The project focuses on educational content related to:

- Artificial Intelligence
- Data
- Cloud Computing

The final solution covers the complete data lifecycle:

**Data Collection → Ingestion → Storage → Profiling → Cleaning → Validation → Transformation → Data Quality → Gold Dataset → API → Web Application**

---

## Project Overview

Educational technical content is distributed across many platforms and stored in different formats and schemas.

TechHub integrates content from multiple sources into a standardized dataset that can be searched and browsed through a single website.

The pipeline:

1. Collects articles from five different sources.
2. Uploads raw data to Azure Data Lake Storage Gen2.
3. Profiles and cleans the collected data.
4. Standardizes records into a common schema.
5. Validates records and separates rejected data.
6. Performs transformations and enrichment.
7. Applies data quality checks.
8. Stores the curated dataset as a Gold Delta table.
9. Exposes the Gold dataset through Databricks SQL and FastAPI.
10. Displays the articles through the deployed TechHub website.

---

# Data Sources

The pipeline integrates content from five sources using source-specific collection methods.

| Source | Collection Method | Description |
| :--- | :--- | :--- |
| **dev.to** | Public API | Technical articles collected using the dev.to API |
| **Pluralsight** | Web Scraping | AI & Data and Cloud articles collected from the Pluralsight Blog |
| **freeCodeCamp** | Web Scraping with Playwright | Educational articles discovered through freeCodeCamp search and article pages |
| **Medium** | Hugging Face Dataset | Medium articles collected from the `BEE-spoke-data/medium-articles-en` dataset |
| **GeeksforGeeks** | Kaggle Dataset | Technical articles collected from the GeeksforGeeks articles dataset |

Each source exposes its data differently, so extraction is source-specific.

After ingestion, all sources pass through the same standardized processing pipeline.

---

# Final Architecture

```text
                         ┌──────────────────────┐
                         │     Data Sources     │
                         │                      │
                         │ dev.to               │
                         │ Pluralsight          │
                         │ freeCodeCamp         │
                         │ Medium               │
                         │ GeeksforGeeks        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Python Ingestion     │
                         │ Pipeline             │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Azure Container Apps │
                         │ Ingestion Job        │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ ADLS Gen2            │
                         │ Raw / Bronze Layer   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Azure Databricks     │
                         │                      │
                         │ Profile              │
                         │ Clean                │
                         │ Validate             │
                         │ Transform            │
                         │ Quality Checks       │
                         └──────────┬───────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                             │
                     ▼                             ▼
          ┌─────────────────────┐       ┌─────────────────────┐
          │ Silver Validated    │       │ Silver Rejected     │
          │ Data                │       │ Data                │
          └──────────┬──────────┘       └─────────────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Gold Delta Dataset  │
          │ processed/final     │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ Databricks SQL      │
          │ Warehouse           │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ FastAPI Backend     │
          │ Azure Container    │
          │ Apps                │
          └──────────┬──────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ TechHub Frontend    │
          │ Azure Static Web    │
          │ Apps                │
          └─────────────────────┘
```

Azure Data Factory orchestrates the ingestion and Databricks processing stages.

---

# Technology Stack

| Area | Technology |
| :--- | :--- |
| Programming | Python |
| Data Processing | Pandas, PySpark |
| Web Scraping | BeautifulSoup, Playwright |
| Dataset Access | Hugging Face Datasets, KaggleHub |
| Cloud Platform | Microsoft Azure |
| Orchestration | Azure Data Factory |
| Ingestion Runtime | Azure Container Apps Jobs |
| Container Registry | Azure Container Registry |
| Data Lake | Azure Data Lake Storage Gen2 |
| Data Processing | Azure Databricks |
| Storage Format | Delta Lake |
| Serving Layer | Databricks SQL Warehouse |
| Backend API | FastAPI |
| Backend Hosting | Azure Container Apps |
| Frontend | HTML, CSS, JavaScript |
| Frontend Hosting | Azure Static Web Apps |
| Source Control | Git / GitHub |
| Frontend Deployment | GitHub Actions |
| Testing | pytest |
| Containerization | Docker |

---

# Pipeline Stages

## 1. Data Extraction

`src/extract.py` contains the source-specific extraction logic.

The extraction methods include:

- REST API requests for dev.to
- HTTP requests and BeautifulSoup for Pluralsight
- Playwright and BeautifulSoup for freeCodeCamp
- Hugging Face `datasets` for Medium
- `kagglehub` for GeeksforGeeks

The extraction process uses incremental behavior where possible.

Previously collected URLs are identified so that already-known articles do not need to be downloaded again during every ingestion run.

---

## 2. Extraction Timeouts

External sources can become slow, rate-limited, or temporarily unavailable.

To prevent one source from blocking the complete ingestion pipeline, source-level hard time budgets are applied.

| Source | Time Budget |
| :--- | ---: |
| dev.to | 600 seconds |
| Pluralsight | 1500 seconds |
| freeCodeCamp | 900 seconds |
| Medium | 600 seconds |
| GeeksforGeeks | 300 seconds |

Timeouts are propagated correctly to the orchestration layer instead of being swallowed by generic exception handling.

This allows the pipeline to terminate or continue according to the configured orchestration behavior rather than appearing stuck indefinitely.

---

# Azure Container Apps Ingestion

The ingestion pipeline is containerized with Docker.

The ingestion image is stored in Azure Container Registry.

Current ingestion image:

```text
techhub-ingestion:v9
```

Azure Container Apps Jobs runs the ingestion container.

The job collects source data and writes the raw results to Azure Data Lake Storage Gen2.

---

# Azure Data Lake Storage

The project uses a layered data architecture in Azure Data Lake Storage Gen2.

## Raw / Bronze

```text
raw/
```

Contains source data collected by the ingestion pipeline.

The raw layer preserves source-specific information before standardization.

---

## Silver

Validated records:

```text
interim/validated/
```

Rejected or quarantined records:

```text
interim/rejected/
```

The Silver layer contains standardized records after cleaning and validation.

Rejected records remain separate so that data-quality failures are traceable.

---

## Gold

```text
processed/final/
```

The final curated dataset is stored as a **Delta table**.

The Gold layer contains one standardized record per unique educational article and is the dataset consumed by the serving layer.

---

# Azure Data Factory Orchestration

Azure Data Factory orchestrates the cloud pipeline.

The master pipeline is:

```text
EdTechMasterPipeline
```

The orchestration flow is:

```text
Set_batch_id
      ↓
Start_ContainerApps_Job
      ↓
Set_Execution_Name
      ↓
Wait_For_Ingestion_Completion
      │
      ├── Check_Ingestion_Status
      │
      └── Wait_Before_Next_Check
              ↓
          Repeat until
       Succeeded or Failed
              ↓
Check_Ingestion_Result
      │
      ├── Success → Run_Databricks_Processing
      │
      └── Failure → Fail_Ingestion
```

## Why Polling Is Used

Starting an Azure Container Apps Job only confirms that the execution was requested.

It does not mean ingestion has finished.

ADF therefore stores the Container Apps execution name and repeatedly checks the status of that exact execution.

Databricks starts only after the ingestion execution reports:

```text
Succeeded
```

If ingestion reports:

```text
Failed
```

the pipeline follows the failure branch instead.

This prevents downstream processing from starting with incomplete raw data.

---

# Databricks Processing

Azure Databricks processes the raw data after successful ingestion.

The main processing notebooks are:

```text
notebooks/
├── 01_profile_raw_data.ipynb
├── 02_clean_validate.ipynb
├── 03_transform.ipynb
└── 04_data_quality_checks.ipynb
```

---

## 1. Raw Data Profiling

The profiling stage analyzes incoming datasets before transformation.

Checks include:

- Dataset size
- Data types
- Null values
- Missing-value percentages
- Unique values
- Duplicate URLs
- Example records
- Important field completeness

This helps identify source-specific data quality issues.

---

## 2. Cleaning and Standardization

The five sources have different original schemas.

Source-specific normalization logic maps the records into a unified structure.

Cleaning includes:

- Text normalization
- Field mapping
- Publication date normalization
- Tag normalization
- Category standardization
- Required-field checks
- URL validation
- Duplicate handling

---

## 3. Validation

Records are validated against the project data-quality requirements.

Valid records are written to:

```text
interim/validated/
```

Invalid records are written to:

```text
interim/rejected/
```

This allows rejected records to remain traceable instead of silently disappearing from the pipeline.

---

## 4. Transformation and Enrichment

Validated records are enriched with additional fields.

The transformation stage creates:

- `word_count`
- `publish_year`
- `is_long_form`

Missing authors can also be standardized to:

```text
Unknown
```

---

## 5. Data Quality Checks

The final processing stage verifies the quality of the curated dataset.

Checks include areas such as:

- Required fields
- URL validity
- Duplicate URLs
- Valid categories
- Content completeness
- Transformation results
- Final schema

The resulting curated dataset is written to the Gold Delta table.

---

# Unified Data Schema

The main standardized fields include:

| Column | Description |
| :--- | :--- |
| `source` | Original content source |
| `category` | AI, Data, or Cloud topic/category |
| `title` | Article title |
| `author` | Article author when available |
| `publication_date` | Normalized publication date when available |
| `description` | Article summary/description |
| `url` | Original article URL |
| `content` | Full article content |
| `tags` | Article tags or keywords |
| `word_count` | Number of words in the article |
| `publish_year` | Publication year derived from the date |
| `is_long_form` | Indicates whether the article is long-form |
| `batch_id` | Pipeline ingestion batch identifier |
| `ingested_at` | Ingestion timestamp |

Some source fields such as author, publication date, or description may not be available from every source. Missing source information is preserved rather than artificially invented.

---

# Gold Serving Layer

The website does not access ADLS directly.

Instead, the project uses the following serving architecture:

```text
Gold Delta
    ↓
Databricks SQL Warehouse
    ↓
FastAPI
    ↓
TechHub Frontend
```

This separates the data storage layer from the application layer.

---

# FastAPI Backend

The backend is implemented in:

```text
api/main.py
```

The FastAPI application queries the Gold dataset through the Databricks SQL Warehouse.

It is deployed independently from the ingestion pipeline.

Backend container image:

```text
techhub-api:v1
```

Backend hosting:

```text
Azure Container Apps
```

---

## Pagination

The API does not retrieve the complete Gold dataset for every website request.

Articles are returned in pages.

Example:

```text
/articles?page=1&limit=20
```

A paginated response contains information such as:

```json
{
  "page": 1,
  "limit": 20,
  "total": 21643,
  "total_pages": 1083,
  "articles": []
}
```

The exact total can change as the ingestion pipeline adds or updates data.

Pagination reduces unnecessary data transfer and improves website performance.

---

## Article Content

The article listing endpoint provides the records required to browse the dataset.

When a user opens an article, the application can retrieve and display its full content.

The user can therefore:

1. Browse articles inside TechHub.
2. Open an article and read its content inside the website.
3. Follow the original article URL to view the content on its source website.

This preserves attribution to the original source while still providing a unified content discovery interface.

---

# TechHub Web Application

The frontend is located under:

```text
frontend/
├── index.html
├── script.js
└── style.css
```

The application uses HTML, CSS, and JavaScript and communicates with the deployed FastAPI backend.

Features include:

- Real Gold dataset records
- Paginated browsing
- 20 records per page
- Previous / Next navigation
- Search
- AI, Data, and Cloud categories
- Article metadata
- Full article content
- Original source links
- Saved articles
- Handling of unavailable author/date information

The frontend does not directly access Azure Data Lake Storage or Databricks credentials.

---

# Azure Deployment

## Backend

The FastAPI backend is packaged using:

```text
Dockerfile.api
```

The Docker image is pushed to Azure Container Registry and deployed to Azure Container Apps.

Deployment flow:

```text
api/main.py
     ↓
Dockerfile.api
     ↓
Azure Container Registry
     ↓
Azure Container Apps
```

Databricks connection information is supplied to the deployed application through environment variables and Azure Container Apps secrets.

Secret values are not stored in the Git repository.

---

## Frontend

The TechHub frontend is deployed using Azure Static Web Apps.

Deployment configuration:

```text
Repository:
TechHub-Group3-EdTech-Content-Data-Pipeline

Branch:
main

App location:
./frontend
```

Azure Static Web Apps uses a GitHub Actions workflow to deploy the frontend from the repository.

Changes pushed to the configured branch can therefore trigger frontend deployment.

---

# End-to-End Flow

The completed system operates as follows:

```text
1. ADF starts the pipeline
             ↓
2. A batch ID is generated
             ↓
3. Azure Container Apps starts the ingestion job
             ↓
4. Articles are collected from the five sources
             ↓
5. Raw data is written to ADLS
             ↓
6. ADF polls the Container Apps execution
             ↓
7. Ingestion succeeds
             ↓
8. ADF starts Databricks processing
             ↓
9. Databricks profiles and cleans the data
             ↓
10. Records are validated
             ↓
11. Invalid records are quarantined
             ↓
12. Valid records are transformed and enriched
             ↓
13. Data quality checks are executed
             ↓
14. Curated data is written to Gold Delta
             ↓
15. Databricks SQL exposes the current Gold data
             ↓
16. FastAPI queries the Gold dataset
             ↓
17. TechHub displays the articles to users
```

The pipeline and deployed website were tested end-to-end.

---

# Project Structure

```text
TechHub-Group3/
│
├── api/
│   └── main.py
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── notebooks/
│   ├── 01_profile_raw_data.ipynb
│   ├── 02_clean_validate.ipynb
│   ├── 03_transform.ipynb
│   └── 04_data_quality_checks.ipynb
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── extract.py
│   ├── profile.py
│   ├── clean.py
│   ├── schema.py
│   ├── transform.py
│   └── upload.py
│
├── tests/
│   ├── test_extract.py
│   ├── test_clean.py
│   ├── test_schema.py
│   └── test_transform.py
│
├── .github/
│   └── workflows/
│       └── Azure Static Web Apps deployment workflow
│
├── Dockerfile
├── Dockerfile.api
├── run_ingestion.py
├── main.py
├── requirements.txt
├── .dockerignore
├── .gitignore
└── README.md
```

Generated raw, interim, and processed datasets are not intended to be committed to Git.

Secrets such as `.env` files and access tokens are also excluded.

---

# Local Setup

## 1. Clone the Repository

```powershell
git clone https://github.com/sarahAAD/TechHub-Group3-EdTech-Content-Data-Pipeline.git
cd TechHub-Group3-EdTech-Content-Data-Pipeline
```

---

## 2. Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

## 4. Install Playwright Chromium

```powershell
playwright install chromium
```

---

## 5. Environment Variables

Local secrets and connection information should be stored in:

```text
.env
```

The `.env` file must not be committed to Git.

The deployed FastAPI application requires Databricks connection settings such as:

```text
DATABRICKS_SERVER_HOSTNAME
DATABRICKS_HTTP_PATH
DATABRICKS_TOKEN
```

Actual secret values are intentionally not included in this repository or documentation.

---

# Running Locally

## Run Tests

```powershell
python -m pytest -v
```

---

## Run Ingestion

```powershell
python run_ingestion.py
```

The main local pipeline can also be run using the project's configured entry point where applicable.

---

## Run FastAPI

From the repository root:

```powershell
uvicorn api.main:app --reload
```

The local API is then available at:

```text
http://127.0.0.1:8000
```

Example local request:

```text
http://127.0.0.1:8000/articles?page=1&limit=20
```

---

## Run the Frontend Locally

Open another terminal:

```powershell
cd frontend
python -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

The production frontend is configured to communicate with the deployed FastAPI service.

---

# Testing

The project uses `pytest` for automated testing.

Run:

```powershell
python -m pytest -v
```

The tests cover pipeline functionality including:

- Source extraction utilities
- Raw data loading
- Source normalization
- Cleaning
- Duplicate handling
- Schema validation
- Rejected records
- Transformation logic
- Final output structure

In addition to unit tests, the project was tested through an end-to-end Azure pipeline execution.

The deployed website was also verified for:

- API connectivity
- Article loading
- Pagination
- Article detail/content display
- Original source links

---

# Monitoring and Failure Handling

Pipeline execution can be monitored through:

- Azure Data Factory Monitor / Debug
- Azure Container Apps execution status
- Container Apps / Log Analytics logs
- Databricks execution output

ADF uses the Container Apps execution status as the orchestration source of truth.

If ingestion fails, the pipeline follows the failure path instead of starting Databricks.

---

# Data Quality Considerations

The five sources contain different levels of metadata completeness and different source structures.

Examples include:

- Some records do not provide an author.
- Some records do not provide a publication date.
- Some records do not provide a description.
- Tags use different source-specific formats.
- Publication dates can use different formats.
- Duplicate URLs may appear across batches.
- Web page structures can change.
- Sources may rate-limit or temporarily reject requests.
- Some source datasets are significantly larger than scraped sources.

The pipeline standardizes available information while preserving genuinely unavailable source metadata.

---

# Security

Sensitive information is not committed to Git.

The project uses:

- `.env` for local development secrets
- `.gitignore` to exclude local secrets
- `.dockerignore` to prevent unnecessary/sensitive files from entering Docker build contexts
- Azure Container Apps secrets for deployed backend credentials

Credentials and access tokens must never be hard-coded in application source files.

---

# Current Deployment

The final deployed solution consists of:

| Component | Deployment |
| :--- | :--- |
| Ingestion | Azure Container Apps Job |
| Raw/Silver/Gold Storage | Azure Data Lake Storage Gen2 |
| Processing | Azure Databricks |
| Orchestration | Azure Data Factory |
| Serving Query Layer | Databricks SQL Warehouse |
| Backend | FastAPI on Azure Container Apps |
| Frontend | Azure Static Web Apps |
| Frontend CI/CD | GitHub Actions |
| Container Images | Azure Container Registry |

---

# Challenges and Lessons Learned

Key challenges encountered during development included:

- Integrating five sources with different schemas and collection methods.
- Handling slow or unreliable external content sources.
- Preventing source timeouts from being swallowed by generic exception handling.
- Managing incremental ingestion and duplicate URLs.
- Ensuring ADF waits for the Container Apps Job to actually finish before starting Databricks.
- Normalizing inconsistent publication dates and tags.
- Handling missing metadata without inventing values.
- Serving a Delta dataset efficiently to a web application.
- Avoiding loading the entire Gold dataset for every website request.
- Separating ingestion, processing, API, and frontend deployment responsibilities.

The final architecture addresses these challenges through source-specific extraction, layered storage, status-based orchestration, Delta storage, API pagination, and independent frontend/backend deployments.

---

# Future Improvements

Potential future improvements include:

- Replace temporary/personal Databricks authentication with a production-oriented identity mechanism where supported.
- Add more advanced API-side search and filtering.
- Add recommendation or AI-powered content discovery.
- Add automated backend container deployment through CI/CD.
- Add pipeline notifications and alerting.
- Add more detailed operational metrics and dashboards.
- Improve article ranking or recommendation using measurable and documented criteria.
- Add additional educational content sources.
- Add automated integration tests for the deployed API and website.
- Optimize Databricks SQL and API caching for larger workloads.

---

# Summary

TechHub demonstrates an end-to-end cloud Data Engineering solution that combines heterogeneous content sources into a standardized and usable educational dataset.

The completed architecture integrates:

```text
Python
+
Docker
+
Azure Container Registry
+
Azure Container Apps
+
Azure Data Lake Storage Gen2
+
Azure Data Factory
+
Azure Databricks
+
Delta Lake
+
Databricks SQL
+
FastAPI
+
Azure Static Web Apps
+
GitHub Actions
```

The result is not only a curated Gold dataset, but a deployed application that allows users to discover and read educational content while retaining access to each article's original source.