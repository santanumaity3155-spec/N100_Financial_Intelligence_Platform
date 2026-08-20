# Repository Structure — N100 Financial Intelligence Platform

## Clean Root Directory Tree

```
N100_Financial_Intelligence_Platform/
├── CLEANUP_SUMMARY.md               # Summary report of repository cleanup & reorganization
├── README.md                       # Master project overview & quickstart guide
├── TODO.md                         # Task checklist & remaining roadmap items
├── NIFTY_SMALL_100.db              # Local SQLite database copy
├── requirements-dashboard.txt      # Python dependencies for Streamlit & API
├── run_etl.py                      # Main ETL pipeline runner entry point
│
├── archive/                        # Archived historical & diagnostic artifacts
│   ├── diagnostics/                # Intermediate diagnostic logs & reports
│   │   ├── data_quality/           # Data quality HTML & JSON reports
│   │   └── kpi_test/               # KPI test outputs
│   └── legacy/                     # Deprecated/historical script versions
│
├── data/                           # Data storage
│   ├── database/                   # Authoritative SQLite database (n100.db)
│   ├── raw/                        # Original scraped/imported datasets
│   └── processed/                  # Processed intermediary data CSVs
│
├── docs/                           # Project documentation & milestone specifications
│   ├── completion_reports/         # Sprint & Module completion reports (Modules 1..9)
│   ├── specifications/             # Specification & status documents
│   └── guides/                     # User & Developer guides
│
├── logs/                           # Runtime log outputs
├── notebooks/                      # Jupyter exploratory notebooks
├── output/                         # Deliverable exports (Excel, CSV summaries)
├── pages/                          # Auxiliary Streamlit pages
│
├── reports/                        # Executive report outputs
│   ├── portfolio/                  # Portfolio summary deliverables
│   ├── sector/                     # Sector report deliverables
│   └── tearsheets/                 # Company PDF tearsheets
│
├── src/                            # Authoritative Production Core Source Code
│   ├── analytics/                  # Financial, Cash Flow & Clustering Engines
│   ├── api/                        # FastAPI REST Web Service & Routers
│   ├── dashboard/                  # Streamlit Multi-Page Application (app.py)
│   ├── database/                   # DB Connection Pools & Query Layer
│   ├── etl/                        # Data Ingestion, Extraction & DQ Pipelines
│   ├── health_score/               # Financial Health Scoring Engine
│   ├── kpi_engine/                 # KPI Calculation Engine
│   ├── nlp/                        # Pros/Cons & Text Intelligence Engine
│   ├── peer_analysis/              # Peer Benchmarking Engine
│   ├── reports/                    # Report & PDF Generation Engine
│   ├── screener/                   # Screener Engine
│   ├── sector_analysis/            # Sector Analysis Engine
│   ├── utils/                      # Common Utilities & Formatting Helpers
│   ├── validation/                 # Schema & Output Data Validators
│   └── visualization/              # Charting & Data Visualization Engine
│
├── tests/                          # Authoritative Pytest Test Suite
│   ├── analytics/                  # Analytics & Calculation Unit/Integration Tests
│   ├── api/                        # REST API Endpoint Tests
│   ├── dashboard/                  # Streamlit Dashboard UI/Component Tests
│   ├── health_score/               # Health Scoring Tests
│   ├── nlp/                        # NLP Engine Tests
│   ├── pipeline/                   # ETL & Data Pipeline Tests
│   ├── reports/                    # Report Generation Tests
│   └── validation/                 # Data Quality & Validation Tests
│
└── tools/                          # Project Utilities & Helper Tooling
    ├── diagnostics/                # Diagnostic scripts & inspection utilities
    ├── legacy/                     # Historical Module 3 variants & workaround scripts
    ├── maintenance/                # Maintenance, linting & docstring utilities
    ├── utilities/                  # Report generators & KPI populator tools
    └── validation/                 # Module validator scripts (validate_module*.py)
```
