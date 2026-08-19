# N100 Financial Intelligence Platform

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/fastapi-0.115%2B-teal)
![Streamlit](https://img.shields.io/badge/streamlit-1.42%2B-red)
![SQLite](https://img.shields.io/badge/sqlite-3.25%2B-green)
![ReportLab](https://img.shields.io/badge/reportlab-5.0%2B-orange)
![License](https://img.shields.io/badge/license-MIT-orange)
![Status](https://img.shields.io/badge/status-production_ready-success)

A production-grade, institutional financial intelligence platform engineered for comprehensive analysis of Nifty 100 constituent companies. The platform seamlessly combines automated ETL pipelines, 30+ financial ratio calculation engines, peer group benchmarking, NLP pros/cons generation, unsupervised machine learning clustering, an interactive Streamlit dashboard, a high-performance FastAPI REST server, and ReportLab PDF tearsheet exports.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Database & ETL Pipeline](#database--etl-pipeline)
- [Streamlit Dashboard](#streamlit-dashboard)
- [FastAPI REST Server](#fastapi-rest-server)
- [API Documentation](#api-documentation)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Reports & Tearsheet Generation](#reports--tearsheet-generation)
- [NLP & Machine Learning](#nlp--machine-learning)
- [Analytics & Intelligence Engines](#analytics--intelligence-engines)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [License & Status](#license--status)

---

## Project Overview

### Purpose & Scope
The N100 Financial Intelligence Platform automates end-to-end fundamental equity research, financial ratio extraction, sector benchmarking, valuation anomaly detection, and client reporting for institutional equity analysts, portfolio managers, and risk research teams.

### Data Universe
- **Companies Analyzed**: 92+ Nifty 100 constituents
- **Sector Breakdown**: 9 Industry Sectors (IT, Banking & Financials, Pharmaceuticals, Consumer Goods, Industrial, Energy, Automobile, Materials, Telecom)
- **Peer Groups**: 13 Benchmarking Peer Groups
- **Historical Horizon**: 12 Fiscal Years (2012–2024)
- **Calculated KPIs**: 30+ Ratios across Profitability, Liquidity, Solvency, Efficiency, Growth, and Valuation

### Major Modules
1. **ETL Data Engine**: 5-stage ingestion, normalization, and validation pipeline.
2. **KPI Engine**: Modular ratio calculation across 10 financial categories.
3. **Peer Analysis & Radar Engine**: Percentile rankings and 10-axis polar radar benchmarking plots.
4. **Valuation & Mispricing Engine**: Automated P/E, P/B, EV/EBITDA flagging against peer medians.
5. **NLP Pros & Cons Generator**: Textual rule engine extracting strengths and risk warnings.
6. **ML Clustering Engine**: K-means behavioral grouping across standardized financial metrics.
7. **FastAPI Server**: High-performance JSON endpoints with Swagger UI and Pydantic v2 validation.
8. **Streamlit Dashboard**: 8 interactive visual analytics screens built with Plotly.
9. **ReportLab Tearsheet Generator**: Institutional single/multi-page PDF report compiler.

---

## Technology Stack

- **Core Backend**: Python 3.10+
- **Database Engine**: SQLite 3.25+
- **Data Manipulation**: Pandas 2.2+, NumPy 2.2+, OpenPyXL 3.1+
- **API Backend**: FastAPI 0.115+, Uvicorn 0.34+, Pydantic v2 2.10+
- **Interactive Dashboard**: Streamlit 1.42+, Plotly 6.0+
- **Machine Learning & NLP**: Scikit-Learn 1.6+, SciPy 1.15+, Custom Pattern Engines
- **PDF Compilation**: ReportLab 5.0+, PyPDF 5.3+
- **Testing & Code Quality**: Pytest 8.3+, Black 25.1+, Ruff 0.9+

---

## Project Structure

```
N100_Financial_Intelligence_Platform/
├── data/                       # Raw source Excel financial statements
├── docs/                       # Platform documentation & Analyst Guide PDF
│   └── analyst_guide.pdf       # Authoritative 14-Page Institutional Analyst Guide
├── output/                     # Exported CSVs, Excel reports & final SQLite DB
│   ├── NIFTY_SMALL_100.db      # Authoritative SQLite Financial Database
│   ├── cashflow_intelligence.xlsx
│   ├── financial_health_scores.csv
│   ├── peer_percentiles.csv
│   ├── valuation_summary.xlsx
│   └── final_deliverables/     # Consolidated 23 project deliverables & manifest
├── reports/                    # Data quality reports, heatmaps & PDF tearsheets
│   ├── correlation_heatmap.png
│   └── tearsheets/             # Generated PDF Tearsheets
├── src/                        # Core Python source package
│   ├── analytics/              # Valuation, Peer, Trend & Cashflow engines
│   ├── api/                    # FastAPI server & REST router endpoints
│   │   ├── main.py             # FastAPI entry point
│   │   └── routers/            # 8 REST endpoints (companies, screener, etc.)
│   ├── dashboard/              # Streamlit multi-page dashboard application
│   │   ├── app.py              # Streamlit app entry point
│   │   ├── components/         # Reusable cards, tables, and Plotly charts
│   │   └── pages/              # 8 Modular page views (01_home.py to 08_reports.py)
│   ├── database/               # SQLite connection & schema models
│   ├── etl/                    # Extraction, normalization, validation & loading
│   ├── health_score/           # Composite financial health engine
│   ├── kpi_engine/             # 30+ financial ratio calculators
│   ├── nlp/                    # Sentiment & pros/cons text rule engine
│   ├── peer_analysis/          # Peer benchmarking & percentiles
│   ├── reports/                # ReportLab PDF tearsheet compilers
│   ├── screener/               # Multi-criteria filter engine
│   ├── sector_analysis/        # Sector heatmaps & aggregations
│   └── utils/                  # Cache, formatter & logging utilities
└── tests/                      # Pytest unit, integration & performance suite
    ├── analytics/              # Analytics engine test suite
    ├── api/                    # FastAPI endpoint test suite
    ├── integration/            # Dashboard & API integration test suite
    ├── nlp/                    # NLP rule engine test suite
    ├── performance/            # Concurrent load test suite
    └── reports/                # ReportLab PDF compiler test suite
```

---

## Installation & Setup

### 1. Environment Requirements
- Operating System: Windows, macOS, or Linux
- Python Version: Python 3.10 or higher

### 2. Virtual Environment Creation
Create and activate an isolated Python virtual environment:

```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### 3. Dependency Installation
Install required dependencies:

```bash
pip install -r requirements-dashboard.txt
```

---

## Database & ETL Pipeline

The N100 Data Engine processes raw multi-sheet Excel workbooks from `data/`, standardizes financial statement line items, computes 30+ ratio metrics, and populates the SQLite database.

### Running the ETL Pipeline

```bash
python run_etl.py
```

### Output Database Location
`output/NIFTY_SMALL_100.db`

---

## Streamlit Dashboard

The N100 Streamlit Dashboard provides an interactive web portal for fundamental equity analysis across 8 specialized pages.

### Launching the Dashboard

Always invoke the exact Streamlit entry point from the repository root:

```bash
streamlit run src/dashboard/app.py
```

### Access URLs
- **Local Portal**: `http://localhost:8501`
- **Network Access**: `http://<your-ip>:8501`

### Navigation Pages
- `01_home.py`: Platform Overview, System Health & Coverage Cards
- `02_profile.py`: Detailed Statements, Ratio Grids & Historical Trends
- `03_screener.py`: Multi-criteria Filter Engine & Preset Scenarios
- `04_peers.py`: Industry Benchmarking, Percentiles & Radar Plot
- `05_trends.py`: 12-Year CAGR Trajectories & Metric Comparison
- `06_sectors.py`: Sector Heatmaps, Rankings & Market Cap Bubbles
- `07_capital.py`: Capital Allocation Distribution & Cash Flow Matrix
- `08_reports.py`: Valuation Flags, PDF Tearsheet Export & Excel Downloads

---

## FastAPI REST Server

The backend API server exposes high-performance REST endpoints built on FastAPI and Uvicorn.

### Launching the API Server

```bash
uvicorn src.api.main:app --reload --port 8000
```

---

## API Documentation

- **Base API URL**: `http://localhost:8000/api/v1`
- **Interactive Swagger UI**: `http://localhost:8000/docs`
- **OpenAPI JSON Schema**: `http://localhost:8000/openapi.json`

### Authoritative Curl Examples

1. **System Health Endpoint**:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

2. **List All Companies**:
   ```bash
   curl http://localhost:8000/api/v1/companies
   ```

3. **Get Specific Company Profile (TCS)**:
   ```bash
   curl http://localhost:8000/api/v1/companies/TCS
   ```

4. **Execute Stock Screener Query**:
   ```bash
   curl "http://localhost:8000/api/v1/screener?min_roe=15&max_pe=25"
   ```

5. **Get Sector Summaries**:
   ```bash
   curl http://localhost:8000/api/v1/sectors
   ```

6. **Get Peer Benchmarking Data**:
   ```bash
   curl http://localhost:8000/api/v1/peers/TCS
   ```

7. **Get Valuation Multiples & Flags**:
   ```bash
   curl http://localhost:8000/api/v1/valuation/TCS
   ```

8. **Get Portfolio Analytics**:
   ```bash
   curl http://localhost:8000/api/v1/portfolio
   ```

---

## Testing & Quality Assurance

The platform features comprehensive test coverage using Pytest across unit, integration, API, NLP, and performance modules.

### Executing Test Suites

```bash
# Run full regression suite (all tests)
python -m pytest tests/ -q

# Run API endpoint tests
python -m pytest tests/api/ -q

# Run Analytics & KPI engine tests
python -m pytest tests/analytics/ -q

# Run NLP rule engine tests
python -m pytest tests/nlp/ -q

# Run ReportLab PDF compilation tests
python -m pytest tests/reports/ -q

# Run Performance & concurrency load tests
python -m pytest tests/performance/ -q

# Run End-to-End integration tests
python -m pytest tests/integration/ -q
```

---

## Reports & Tearsheet Generation

The platform features an institutional PDF tearsheet generator powered by ReportLab.

- **Tearsheets Output**: `reports/tearsheets/`
- **Peer Reports Output**: `output/peer_reports/`
- **Excel Valuation Summary**: `output/valuation_summary.xlsx`
- **Analyst Guide PDF**: `docs/analyst_guide.pdf`

### Generating Tearsheets Programmatically

```bash
python -m src.reports.tearsheet_generator --all
```

---

## NLP & Machine Learning

- **NLP Pros & Cons Engine** (`src/nlp/pros_cons_generator.py`): Automatically evaluates company metrics against 50+ quantitative financial rules to output human-readable investment pros and cons to `output/pros_cons_generated.csv`.
- **ML Behavioral Clustering** (`src/analytics/clustering.py`): Performs K-Means clustering across normalized financial ratios to uncover organic peer groups beyond traditional sector definitions.

---

## Analytics & Intelligence Engines

- **Ratio Engine**: Calculates 30+ ratios across 12 fiscal years.
- **Health Score Engine**: Composite 0-100 financial health grading.
- **Peer Percentile Engine**: 0-100th percentile rank across peer groups.
- **Valuation Flagging**: Automated Overvalued/Undervalued tagging.
- **Capital Allocation Matrix**: Categorizes cash flow deployment into CapEx Reinvestment, Shareholder Returns, or Debt Paydown.

---

## Troubleshooting & FAQ

| Problem / Error | Cause | Recommended Solution |
|:---|:---|:---|
| Database Not Found | Missing `output/NIFTY_SMALL_100.db` | Run `python run_etl.py` to populate SQLite database. |
| Streamlit Entry Error | Running generic `streamlit run app.py` | Run exact path: `streamlit run src/dashboard/app.py`. |
| Port 8501 Bound | Previous Streamlit instance still running | Kill process on 8501 or use `streamlit run src/dashboard/app.py --server.port 8502`. |
| Port 8000 Bound | FastAPI server active in background | Terminate background process on port 8000. |
| API 404 Error | API server not running | Start backend: `uvicorn src.api.main:app --reload --port 8000`. |
| ModuleNotFoundError | Virtualenv package missing | Run `pip install -r requirements-dashboard.txt`. |

---

## License & Status

- **Status**: Production Ready (Module 6H Complete)
- **License**: MIT License
- **Maintainer**: Bluestock Financial Analytics Team