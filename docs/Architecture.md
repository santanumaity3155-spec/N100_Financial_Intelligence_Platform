# N100 Financial Intelligence Platform - Technical Architecture

**Version**: 1.0.0  
**Last Updated**: August 6, 2026  
**Platform**: N100 Financial Intelligence Platform  
**Organization**: Bluestock

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Database Architecture](#database-architecture)
3. [Analytics Engine](#analytics-engine)
4. [Dashboard Architecture](#dashboard-architecture)
5. [ETL Pipeline](#etl-pipeline)
6. [Folder Structure](#folder-structure)
7. [Caching Strategy](#caching-strategy)
8. [Data Flow](#data-flow)
9. [Architecture Diagram](#architecture-diagram)

---

## System Overview

The N100 Financial Intelligence Platform is a production-grade financial analytics system built with a modular, layered architecture. The system processes financial data from Excel files through an ETL pipeline, stores it in a SQLite database, and presents it through an interactive Streamlit dashboard.

### Key Design Principles

1. **Separation of Concerns**: Clear boundaries between data ingestion, processing, storage, and presentation
2. **Modularity**: Independent modules for ETL, analytics, and dashboard
3. **Scalability**: Designed to handle 10,000+ records with optimal performance
4. **Maintainability**: Well-documented code with comprehensive logging
5. **Testability**: Unit tests and integration tests for all components
6. **Performance**: Caching, indexing, and query optimization

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│              Streamlit Dashboard (8 Pages)                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Analytics Layer                           │
│  ┌────────────┬────────────┬────────────┬──────────────┐   │
│  │ KPI Engine │ Peer Engine│ Valuation  │ Health Score  │   │
│  │ (30+ KPIs) │(13 Groups) │(92 Records)│ (Composite)   │   │
│  └────────────┴────────────┴────────────┴──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Access Layer                         │
│              Database Utils & Caching                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Database Layer                            │
│              SQLite (20 Tables, 10K+ Records)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    ETL Pipeline                              │
│  Extract → Normalize → Validate → Transform → Load          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
│              12 Excel Files (Nifty 100 Data)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Architecture

### Database Technology

- **Type**: SQLite 3.25+
- **Location**: `data/database/n100.db`
- **Size**: 2.18 MB
- **Character Set**: UTF-8
- **Foreign Keys**: Enabled
- **Indexes**: Optimized for query performance

### Database Schema

#### Core Tables (20 Total)

**1. companies** (92 records)
- Primary company information
- Fields: company_id, name, ticker, sector, industry, description
- Indexes: company_id (PK), ticker, sector

**2. profit_loss** (1,263 records)
- Profit & Loss statements
- Fields: company_id, period, revenue, expenses, net_profit, gross_profit
- Indexes: (company_id, period), company_id

**3. balance_sheet** (1,225 records)
- Balance sheet data
- Fields: company_id, period, total_assets, total_liabilities, equity
- Indexes: (company_id, period), company_id

**4. cash_flow** (1,164 records)
- Cash flow statements
- Fields: company_id, period, operating_cf, investing_cf, financing_cf
- Indexes: (company_id, period), company_id

**5. financial_ratios** (1,065 records)
- Calculated financial ratios
- Fields: company_id, period, roe, roce, pe_ratio, pb_ratio, debt_equity
- Indexes: (company_id, period), company_id

**6. financial_kpis** (1,164 records)
- Key Performance Indicators
- Fields: company_id, period, kpi_name, kpi_value, kpi_category
- Indexes: (company_id, period), company_id, kpi_name

**7. sectors** (92 records)
- Sector classifications
- Fields: sector_id, sector_name, sector_code, description
- Indexes: sector_id (PK), sector_code

**8. stock_prices** (5,520 records)
- Historical stock prices
- Fields: company_id, date, open, high, low, close, volume
- Indexes: (company_id, date), company_id

**9. market_cap** (92 records)
- Market capitalization
- Fields: company_id, period, market_cap, shares_outstanding
- Indexes: company_id (PK)

**10. peer_groups** (56 records)
- Peer group assignments
- Fields: company_id, peer_group_id, sector, industry
- Indexes: company_id, peer_group_id

**11. peer_benchmarks** (13 records)
- Peer group benchmarks
- Fields: peer_group_id, metric_name, avg_value, median_value, percentile_25, percentile_75
- Indexes: peer_group_id (PK)

**12. documents** (1,585 records)
- Document references
- Fields: company_id, doc_type, doc_period, file_path
- Indexes: company_id, doc_type

**13. pros_cons** (5 records)
- Pros and cons analysis
- Fields: company_id, pros, cons, overall_rating
- Indexes: company_id (PK)

**14. analysis** (5 records)
- Analysis metadata
- Fields: analysis_id, analysis_type, parameters, results
- Indexes: analysis_id (PK)

**15. annual_reports** (1,533 records)
- Annual report data
- Fields: company_id, year, report_type, report_data
- Indexes: (company_id, year), company_id

**16. valuation_summary** (92 records)
- Valuation metrics
- Fields: company_id, pe_ratio, pb_ratio, ev_ebitda, valuation_flag
- Indexes: company_id (PK)

**17. valuation_flags** (92 records)
- Valuation flags
- Fields: company_id, flag_type, flag_severity, flag_message
- Indexes: company_id, flag_type

**18. financial_health_scores** (92 records)
- Health scores
- Fields: company_id, score, grade, profitability_score, liquidity_score
- Indexes: company_id (PK)

**19. sector_rankings** (9 records)
- Sector performance rankings
- Fields: sector_id, period, avg_roe, avg_roce, avg_pe
- Indexes: sector_id (PK)

**20. etl_audit** (12 records)
- ETL pipeline audit log
- Fields: run_id, run_date, status, records_loaded, errors
- Indexes: run_id (PK)

### Entity Relationship Diagram

```
┌─────────────┐
│  companies  │ (1)
└──────┬──────┘
       │
       ├──────────────────┬──────────────────┬──────────────────┐
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│profit_loss  │   │balance_sheet│   │ cash_flow   │   │stock_prices │
│  (n)        │   │  (n)        │   │  (n)        │   │  (n)        │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
       │                  │                  │                  │
       └──────────────────┴──────────────────┴──────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │financial_ratios │
                   │  financial_kpis │
                   └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │  peer_groups    │
                   │peer_benchmarks  │
                   └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │valuation_summary│
                   │valuation_flags  │
                   └─────────────────┘
```

### Database Connection Management

**Connection Pool**: Singleton pattern
**Connection Timeout**: 30 seconds
**Auto-commit**: Enabled
**Foreign Keys**: Enabled via PRAGMA
**Journal Mode**: WAL (Write-Ahead Logging)
**Synchronous**: NORMAL

**Connection Code**:
```python
# src/database/connection.py
from contextlib import contextmanager

@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect('data/database/n100.db', timeout=30)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
```

---

## Analytics Engine

### KPI Engine

**Location**: `src/kpi_engine/`

**Purpose**: Calculate 30+ financial KPIs from raw financial data

**Modules**:
- **calculator.py**: Main KPI calculation orchestrator
- **profitability.py**: ROE, ROCE, Net Margin, Operating Margin
- **liquidity.py**: Current Ratio, Quick Ratio, Cash Ratio
- **leverage.py**: Debt-to-Equity, Interest Coverage, Debt Ratio
- **efficiency.py**: Asset Turnover, Inventory Turnover, Receivables Turnover
- **valuation.py**: P/E, P/B, EV/EBITDA, Market Cap
- **cashflow.py**: Operating CF Ratio, Free Cash Flow
- **growth.py**: Revenue Growth, Profit Growth, CAGR
- **validator.py**: KPI validation and range checking
- **formatter.py**: KPI formatting and display

**Calculation Flow**:
```
Raw Data (profit_loss, balance_sheet, cash_flow)
    ↓
KPI Calculator (calculator.py)
    ↓
Category-specific Calculators (profitability.py, etc.)
    ↓
Validated KPIs (validator.py)
    ↓
Formatted Output (formatter.py)
    ↓
Database (financial_kpis table)
```

**Example Calculation**:
```python
# ROE Calculation
def calculate_roe(net_profit, equity):
    """Calculate Return on Equity"""
    if equity == 0:
        return 0
    return (net_profit / equity) * 100
```

### Peer Analysis Engine

**Location**: `src/peer_analysis/`

**Purpose**: Benchmark companies against industry peers

**Modules**:
- **benchmarking.py**: Peer group benchmarking
- **comparison.py**: Side-by-side comparison
- **percentile.py**: Percentile calculations
- **radar.py**: Radar chart data preparation

**Peer Groups** (13 total):
1. Information Technology
2. Financial Services
3. Energy
4. Pharmaceuticals
5. Automobile
6. FMCG
7. Metals & Mining
8. Telecom
9. Infrastructure
10. Consumer Goods
11. Healthcare
12. Real Estate
13. Others

**Benchmarking Process**:
```
Company Selection
    ↓
Peer Group Assignment (based on sector)
    ↓
Metric Calculation (ROE, ROCE, etc.)
    ↓
Peer Statistics (avg, median, percentiles)
    ↓
Percentile Ranking
    ↓
Radar Chart Data
```

### Valuation Engine

**Location**: `src/analytics/valuation.py`

**Purpose**: Calculate valuation metrics and generate flags

**Metrics Calculated**:
- P/E Ratio (Price-to-Earnings)
- P/B Ratio (Price-to-Book)
- EV/EBITDA (Enterprise Value to EBITDA)
- Market Capitalization
- PEG Ratio (P/E to Growth)
- Dividend Yield

**Valuation Flags**:
- Overvalued (P/E > sector_avg * 1.5)
- Undervalued (P/E < sector_avg * 0.5)
- High Debt (Debt/Equity > 2)
- Low Liquidity (Current Ratio < 1)
- Fair Valued (all metrics normal)

**Outputs**:
- `output/valuation_summary.xlsx`: Comprehensive valuation report
- `output/valuation_flags.csv`: Flagged companies with details

### Health Score Engine

**Location**: `src/health_score/`

**Purpose**: Calculate composite financial health score

**Components**:
- **Profitability Score** (40% weight)
- **Liquidity Score** (20% weight)
- **Leverage Score** (20% weight)
- **Efficiency Score** (20% weight)

**Grading**:
- A: 90-100 (Excellent)
- B: 80-89 (Good)
- C: 70-79 (Average)
- D: 60-69 (Below Average)
- F: <60 (Poor)

### Screener Engine

**Location**: `src/screener/`

**Purpose**: Filter companies based on financial criteria

**Modules**:
- **engine.py**: Main screening logic
- **filters.py**: Filter definitions
- **exporter.py**: CSV export functionality
- **presets.py**: Pre-built screening strategies
- **ranking.py**: Result ranking and sorting

**Filter Categories**:
- Profitability (ROE, ROCE, margins)
- Liquidity (Current Ratio, Quick Ratio)
- Leverage (Debt/Equity, Interest Coverage)
- Efficiency (Asset Turnover, Inventory Turnover)
- Valuation (P/E, P/B, EV/EBITDA)
- Growth (Revenue Growth, Profit Growth)

**Presets**:
- Value Stocks
- Growth Stocks
- Quality Stocks
- Dividend Stocks

### Sector Analysis Engine

**Location**: `src/sector_analysis/`

**Purpose**: Sector-wise performance analysis

**Modules**:
- **sector_summary.py**: Sector aggregation
- **rankings.py**: Sector rankings
- **visualization.py**: Sector charts
- **comparison.py**: Sector comparison

**Metrics**:
- Average ROE, ROCE
- Average P/E, P/B
- Market Cap distribution
- Performance rankings

---

## Dashboard Architecture

### Application Structure

**Main Application**: `src/dashboard/app.py`

**Entry Point**:
```python
def main():
    initialize_logging()
    configure_page()
    render_sidebar()
    render_main_content()
```

**Page Routing**: Streamlit multi-page app
**Navigation**: Sidebar-based
**State Management**: Streamlit session state
**Caching**: @st.cache_data with 600s TTL

### Dashboard Pages

#### 1. Home Dashboard (`pages/01_home.py`)

**Purpose**: Platform overview and quick navigation

**Components**:
- Welcome message
- Platform metrics
- Quick company search
- Database status
- Navigation guide

**Data Sources**: companies, financial_kpis, market_cap

**Cache TTL**: 600 seconds

#### 2. Company Profile (`pages/02_profile.py`)

**Purpose**: Detailed company analysis

**Components**:
- Company info header
- Financial statements (P&L, BS, CF)
- Financial ratios (30+ KPIs)
- Historical charts
- Peer summary

**Data Sources**: profit_loss, balance_sheet, cash_flow, financial_ratios, financial_kpis

**Cache TTL**: 600 seconds

#### 3. Stock Screener (`pages/03_screener.py`)

**Purpose**: Filter and screen companies

**Components**:
- Filter panel (20+ criteria)
- Results table
- Pre-built presets
- CSV export

**Data Sources**: financial_ratios, financial_kpis, companies

**Cache TTL**: 300 seconds (frequent updates)

#### 4. Peer Comparison (`pages/04_peers.py`)

**Purpose**: Benchmark against peers

**Components**:
- Company selector
- Peer group display
- Radar chart
- Metrics comparison table
- Percentile rankings

**Data Sources**: peer_groups, financial_ratios, financial_kpis, peer_benchmarks

**Cache TTL**: 600 seconds

#### 5. Trend Analysis (`pages/05_trends.py`)

**Purpose**: Historical performance tracking

**Components**:
- Company selector
- Metric selector (up to 5)
- Multi-line chart
- Growth rate calculations
- CAGR display

**Data Sources**: financial_kpis, profit_loss, balance_sheet, cash_flow

**Cache TTL**: 600 seconds

#### 6. Sector Analysis (`pages/06_sectors.py`)

**Purpose**: Sector-wise analysis

**Components**:
- Sector selector
- Sector performance metrics
- Bubble charts
- Rankings table
- Distribution analysis

**Data Sources**: sectors, financial_ratios, market_cap, sector_rankings

**Cache TTL**: 600 seconds

#### 7. Capital Allocation (`pages/07_capital.py`)

**Purpose**: Cash flow and capital structure analysis

**Components**:
- Cash flow statement
- Treemap visualization
- Capital structure metrics
- Dividend analysis

**Data Sources**: cash_flow, balance_sheet

**Cache TTL**: 600 seconds

#### 8. Annual Reports (`pages/08_reports.py`)

**Purpose**: Comprehensive report generation

**Components**:
- Company search
- Report generation
- Multi-section display
- Export functionality

**Data Sources**: documents, profit_loss, balance_sheet, cash_flow, ratios

**Cache TTL**: 600 seconds

### Dashboard Utilities

**Location**: `src/dashboard/utils/`

**Modules**:
- **db.py**: Database access layer
- **formatter.py**: Data formatting utilities
- **helpers.py**: Helper functions
- **cache.py**: Caching utilities

**Database Utils**:
```python
# Key functions in db.py
def get_companies() -> List[Dict]
def get_company_by_id(company_id: str) -> Dict
def get_financial_ratios(company_id: str, period: str) -> pd.DataFrame
def get_peer_groups(company_id: str) -> List[Dict]
def get_sector_performance(sector: str) -> pd.DataFrame
def get_valuation_metrics(company_id: str) -> Dict
```

---

## ETL Pipeline

### Pipeline Architecture

**Location**: `src/etl/`

**Orchestrator**: `pipeline.py`

**Stages**:
1. Extract
2. Normalize
3. Validate
4. Transform
5. Load

### Stage 1: Extraction

**Module**: `extract.py`

**Class**: `DataExtractor`

**Functionality**:
- Reads Excel files from `data/raw/`
- Handles multiple sheet formats
- Validates file existence
- Extracts to pandas DataFrames

**Input**: 12 Excel files
**Output**: Raw DataFrames

**Supported Files**:
- companies.xlsx
- profit_loss.xlsx
- balance_sheet.xlsx
- cash_flow.xlsx
- ratios.xlsx
- stock_prices.xlsx
- market_cap.xlsx
- sectors.xlsx
- peer_groups.xlsx
- documents.xlsx
- pros_cons.xlsx
- annual_reports.xlsx

### Stage 2: Normalization

**Module**: `normalizer.py`

**Class**: `DataNormalizer`

**Functionality**:
- Standardizes company IDs (uppercase, removes special chars)
- Normalizes year formats (FY2024 → 2024-FY)
- Cleans numeric columns (removes commas, handles negatives)
- Removes duplicates based on business keys
- Handles missing values

**Input**: Raw DataFrames
**Output**: Cleaned DataFrames

**Normalization Rules**:
```python
# Company ID: UPPERCASE, alphanumeric only
company_id = re.sub(r'[^A-Z0-9]', '', company_id.upper())

# Year: FY2024 → 2024-FY
year = re.sub(r'FY(\d{4})', r'\1-FY', year)

# Numeric: Remove commas, convert to float
value = float(str(value).replace(',', '').replace(' ', ''))
```

### Stage 3: Validation

**Module**: `validator.py`

**Class**: `DataValidator`

**Functionality**:
- Checks required columns exist
- Detects missing values with thresholds
- Identifies duplicate records
- Validates data types
- Generates validation reports (HTML/JSON)

**Input**: Cleaned DataFrames
**Output**: Validation reports, validated DataFrames

**Validation Checks**:
1. **Column Validation**: Required columns present
2. **Missing Values**: Threshold-based detection
3. **Duplicate Detection**: Based on business keys
4. **Data Type Validation**: Correct types for columns
5. **Range Validation**: Values within expected ranges
6. **Referential Integrity**: Foreign key validation

**Validation Report**:
- HTML report with visual indicators
- JSON report for programmatic access
- Summary statistics
- Failed records list

### Stage 4: Transformation

**Module**: `transform.py`

**Class**: `DataTransformer`

**Functionality**:
- Applies business rules
- Calculates derived metrics
- Ensures data consistency
- Prepares data for loading

**Input**: Validated DataFrames
**Output**: Transformed DataFrames

**Transformations**:
- Calculated fields (e.g., total_assets = current_assets + fixed_assets)
- Derived metrics (e.g., profit_margin = net_profit / revenue)
- Data type conversions
- Format standardization

### Stage 5: Loading

**Module**: `load.py`

**Class**: `DataLoader`

**Functionality**:
- Creates database tables with schema
- Loads data with chunking
- Handles foreign key constraints
- Verifies row counts
- Generates load audit reports

**Input**: Transformed DataFrames
**Output**: SQLite database, audit reports

**Loading Strategy**:
- **Chunking**: 1000 rows per chunk for large datasets
- **Transaction**: Single transaction per table
- **Foreign Keys**: Disabled during load, enabled after
- **Verification**: Row count validation
- **Audit**: Complete audit trail

**Load Audit Report**:
- Tables loaded
- Records loaded per table
- Load time
- Errors encountered
- Success/failure status

### Data Quality

**Module**: `data_quality.py`

**Functionality**:
- Generates data quality reports
- Tracks data lineage
- Monitors data freshness
- Alerts on quality issues

**Reports**:
- HTML quality dashboard
- JSON quality metrics
- CSV quality logs

---

## Folder Structure

```
N100_Financial_Intelligence_Platform/
│
├── data/                           # Data storage
│   ├── database/                   # SQLite database
│   │   └── n100.db                # Main database (2.18 MB)
│   └── raw/                        # Raw Excel files
│       ├── companies.xlsx         # 92 companies
│       ├── profit_loss.xlsx       # 1,263 records
│       ├── balance_sheet.xlsx     # 1,225 records
│       ├── cash_flow.xlsx         # 1,164 records
│       ├── ratios.xlsx            # 1,065 records
│       ├── stock_prices.xlsx      # 5,520 records
│       ├── market_cap.xlsx        # 92 records
│       ├── sectors.xlsx           # 92 records
│       ├── peer_groups.xlsx       # 56 records
│       ├── documents.xlsx         # 1,585 records
│       ├── pros_cons.xlsx         # 5 records
│       └── annual_reports.xlsx    # 1,533 records
│
├── docs/                           # Documentation
│   ├── User_Guide.md              # User documentation
│   ├── Architecture.md            # This file
│   ├── Project_Summary.md         # Project overview
│   ├── Sprint4_Retrospective.md   # Sprint retrospective
│   ├── screenshots/               # Dashboard screenshots
│   ├── manual_data_review.md
│   ├── etl_validation_summary.md
│   └── SPRINT1_REVIEW.md
│
├── logs/                           # Application logs
│   └── dashboard.log
│
├── notebooks/                      # SQL queries
│   └── exploratory_queries.sql
│
├── output/                         # Generated outputs
│   ├── valuation_summary.xlsx     # Valuation report
│   ├── valuation_flags.csv        # Valuation flags
│   ├── financial_health_scores.csv # Health scores
│   ├── peer_percentiles.csv       # Peer benchmarks
│   ├── peer_reports/              # Peer reports
│   └── radar_charts/              # Radar charts
│
├── pages/                          # Dashboard pages
│   ├── 01_home.py
│   ├── 02_profile.py
│   ├── 03_screener.py
│   ├── 04_peers.py
│   ├── 05_trends.py
│   ├── 06_sectors.py
│   ├── 07_capital.py
│   └── 08_reports.py
│
├── reports/                        # Generated reports
│   └── data_quality_report_*.html
│
├── src/                            # Source code
│   ├── config/                     # Configuration
│   │   ├── column_mappings.py     # Column name mappings
│   │   ├── constants.py           # Application constants
│   │   ├── logging_config.py      # Logging configuration
│   │   └── settings.py            # Application settings
│   │
│   ├── database/                   # Database layer
│   │   ├── connection.py          # Connection management
│   │   ├── models.py              # Data models
│   │   ├── schema.py              # Schema definitions
│   │   └── seed.py                # Database seeding
│   │
│   ├── etl/                        # ETL pipeline
│   │   ├── extract.py             # Data extraction
│   │   ├── normalizer.py          # Data normalization
│   │   ├── validator.py           # Data validation
│   │   ├── transform.py           # Data transformation
│   │   ├── load.py                # Data loading
│   │   ├── pipeline.py            # Pipeline orchestrator
│   │   └── data_quality.py        # Data quality checks
│   │
│   ├── kpi_engine/                 # KPI calculations
│   │   ├── calculator.py          # Main calculator
│   │   ├── profitability.py       # Profitability KPIs
│   │   ├── liquidity.py           # Liquidity KPIs
│   │   ├── leverage.py            # Leverage KPIs
│   │   ├── efficiency.py          # Efficiency KPIs
│   │   ├── valuation.py           # Valuation KPIs
│   │   ├── cashflow.py            # Cash flow KPIs
│   │   ├── growth.py              # Growth KPIs
│   │   ├── validator.py           # KPI validation
│   │   └── formatter.py           # KPI formatting
│   │
│   ├── analytics/                  # Advanced analytics
│   │   ├── valuation.py           # Valuation engine
│   │   ├── peer.py                # Peer analysis
│   │   ├── radar.py               # Radar charts
│   │   ├── trends.py              # Trend analysis
│   │   ├── sector.py              # Sector analysis
│   │   └── ratio_engine.py        # Ratio calculations
│   │
│   ├── screener/                   # Stock screener
│   │   ├── engine.py              # Screening engine
│   │   ├── filters.py             # Filter definitions
│   │   ├── exporter.py            # CSV export
│   │   ├── presets.py             # Pre-built presets
│   │   └── ranking.py             # Result ranking
│   │
│   ├── peer_analysis/              # Peer comparison
│   │   ├── benchmarking.py        # Benchmarking logic
│   │   ├── comparison.py          # Comparison logic
│   │   ├── percentile.py          # Percentile calculations
│   │   └── radar.py               # Radar chart data
│   │
│   ├── sector_analysis/            # Sector analysis
│   │   ├── sector_summary.py      # Sector aggregation
│   │   ├── rankings.py            # Sector rankings
│   │   └── visualization.py       # Sector charts
│   │
│   ├── health_score/               # Health scoring
│   │   ├── engine.py              # Scoring engine
│   │   ├── scoring.py             # Scoring logic
│   │   ├── grading.py             # Grade assignment
│   │   └── rules.py               # Scoring rules
│   │
│   ├── reports/                    # Report generation
│   │   ├── company_report.py      # Company reports
│   │   ├── excel_export.py        # Excel export
│   │   ├── pdf_export.py          # PDF export
│   │   └── sector_report.py       # Sector reports
│   │
│   ├── visualization/              # Chart utilities
│   │   ├── bar.py                 # Bar charts
│   │   ├── line.py                # Line charts
│   │   ├── radar.py               # Radar charts
│   │   ├── treemap.py             # Treemap charts
│   │   ├── waterfall.py           # Waterfall charts
│   │   ├── heatmap.py             # Heatmaps
│   │   └── gauges.py              # Gauge charts
│   │
│   ├── alerts/                     # Alert system
│   │   ├── alerts.py              # Alert management
│   │   ├── rules.py               # Alert rules
│   │   ├── watchlist.py           # Watchlist management
│   │   └── notification.py        # Notifications
│   │
│   ├── utils/                      # Utilities
│   │   ├── cache.py               # Caching utilities
│   │   ├── formatter.py           # Data formatting
│   │   ├── helpers.py             # Helper functions
│   │   ├── logger.py              # Logging utilities
│   │   └── parser.py              # Data parsing
│   │
│   ├── dashboard/                  # Dashboard framework
│   │   ├── app.py                 # Main application
│   │   ├── utils.py               # Dashboard utilities
│   │   ├── components/            # Reusable components
│   │   ├── pages/                 # Page modules
│   │   └── utils/                 # Dashboard utils
│   │
│   └── tests/                      # Unit tests
│       ├── test_etl.py
│       ├── test_database.py
│       ├── test_kpi.py
│       └── test_dashboard.py
│
├── .gitignore
├── README.md                       # Project README
├── requirements.txt                # Python dependencies
├── requirements-dashboard.txt      # Dashboard dependencies
├── run_etl.py                      # ETL runner
├── populate_financial_kpis.py      # KPI calculator
└── MODULE_*_COMPLETION_REPORT.md   # Sprint reports
```

---

## Caching Strategy

### Cache Layers

**1. Database Query Cache**
- **Location**: `src/dashboard/utils/db.py`
- **Mechanism**: Streamlit @st.cache_data
- **TTL**: 600 seconds (10 minutes)
- **Purpose**: Cache database query results

**2. Computation Cache**
- **Location**: `src/utils/cache.py`
- **Mechanism**: In-memory dictionary
- **TTL**: 300-600 seconds
- **Purpose**: Cache expensive computations

**3. Visualization Cache**
- **Location**: Dashboard pages
- **Mechanism**: Streamlit @st.cache_data
- **TTL**: 600 seconds
- **Purpose**: Cache chart data

### Cache Configuration

```python
# Cache TTL by data type
CACHE_TTL = {
    'companies': 3600,           # 1 hour (rarely changes)
    'financial_ratios': 600,     # 10 minutes
    'financial_kpis': 600,       # 10 minutes
    'peer_groups': 3600,         # 1 hour
    'sectors': 3600,             # 1 hour
    'stock_prices': 300,         # 5 minutes (frequent updates)
    'market_cap': 1800,          # 30 minutes
}
```

### Cache Invalidation

**Automatic Invalidation**:
- TTL expiration
- Data update triggers

**Manual Invalidation**:
```python
# Clear specific cache
st.cache_data.clear()

# Or restart dashboard
```

### Cache Benefits

- **Performance**: 90%+ cache hit rate
- **User Experience**: Faster page loads
- **Database Load**: Reduced query frequency
- **Scalability**: Supports concurrent users

---

## Data Flow

### ETL Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EXTRACT                                                    │
│    Input: 12 Excel files (data/raw/)                         │
│    Process: Read Excel, validate structure                   │
│    Output: Raw DataFrames                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. NORMALIZE                                                  │
│    Input: Raw DataFrames                                     │
│    Process: Clean IDs, normalize years, clean numbers        │
│    Output: Cleaned DataFrames                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. VALIDATE                                                   │
│    Input: Cleaned DataFrames                                 │
│    Process: Check columns, missing values, duplicates        │
│    Output: Validation reports, validated DataFrames          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. TRANSFORM                                                  │
│    Input: Validated DataFrames                               │
│    Process: Business rules, derived metrics                  │
│    Output: Transformed DataFrames                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LOAD                                                       │
│    Input: Transformed DataFrames                             │
│    Process: Create tables, load data, verify counts          │
│    Output: SQLite database, audit reports                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. KPI CALCULATION                                            │
│    Input: Database tables                                    │
│    Process: Calculate 30+ KPIs                               │
│    Output: financial_kpis table, health scores               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. ANALYTICS                                                  │
│    Input: Database tables                                    │
│    Process: Peer analysis, valuation, sector analysis        │
│    Output: Peer benchmarks, valuation flags, sector rankings │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. DASHBOARD                                                  │
│    Input: Database queries                                   │
│    Process: Streamlit rendering, interactive charts          │
│    Output: Web dashboard (8 pages)                           │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard Data Flow

```
User Request (Page Navigation)
    │
    ▼
Page Module (e.g., pages/01_home.py)
    │
    ▼
Database Utils (src/dashboard/utils/db.py)
    │
    ├─→ Check Cache
    │   │
    │   ├─→ Cache Hit → Return Cached Data
    │   │
    │   └─→ Cache Miss → Continue
    │
    ├─→ Query Database
    │   │
    │   └─→ SQL Query → SQLite
    │
    ├─→ Process Data
    │   │
    │   └─→ Pandas transformations
    │
    ├─→ Cache Results
    │
    └─→ Return Data
        │
        ▼
Visualization (Plotly charts)
    │
    ▼
Streamlit Rendering
    │
    ▼
User Interface (Browser)
```

### Request Flow Example

**User Action**: Select "TCS" on Profile page

**Flow**:
1. User selects "TCS" from dropdown
2. Streamlit triggers page rerun
3. `pages/02_profile.py` calls `get_company_by_id("TCS")`
4. `db.py` checks cache for "TCS" data
5. Cache miss → Query database
6. SQL: `SELECT * FROM companies WHERE company_id = 'TCS'`
7. SQL: `SELECT * FROM profit_loss WHERE company_id = 'TCS'`
8. SQL: `SELECT * FROM balance_sheet WHERE company_id = 'TCS'`
9. SQL: `SELECT * FROM financial_ratios WHERE company_id = 'TCS'`
10. Process data with Pandas
11. Cache results (600s TTL)
12. Return data to page
13. Page renders charts and tables
14. Display to user

**Time Breakdown**:
- Cache check: <1ms
- Database queries: ~50ms
- Data processing: ~20ms
- Chart rendering: ~100ms
- Total: ~170ms

---

## Architecture Diagram

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                            │
│                    (Web Browser - Streamlit)                       │
└────────────────────────────┬───────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Streamlit Dashboard (app.py)                     │ │
│  │  ┌──────────┬──────────┬──────────┬──────────┬──────────┐   │ │
│  │  │  Home    │ Profile  │Screener  │  Peers   │  Trends  │   │ │
│  │  ├──────────┼──────────┼──────────┼──────────┼──────────┤   │ │
│  │  │ Sectors  │ Capital  │ Reports  │          │          │   │ │
│  │  └──────────┴──────────┴──────────┴──────────┴──────────┘   │ │
│  │  State Management: Session State                              │ │
│  │  Caching: @st.cache_data (600s TTL)                          │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬───────────────────────────────────────┘
                             │ API Calls
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    ANALYTICS LAYER                                 │
│  ┌────────────────┬────────────────┬──────────────────────────┐   │
│  │  KPI Engine    │  Peer Engine   │  Valuation Engine         │   │
│  │  (30+ KPIs)    │  (13 Groups)   │  (92 Records)             │   │
│  │  • Profitability│  • Benchmarking│  • P/E, P/B, EV/EBITDA   │   │
│  │  • Liquidity    │  • Percentiles │  • Valuation Flags        │   │
│  │  • Leverage     │  • Radar Charts│  • Excel Export           │   │
│  │  • Efficiency   │                │                           │   │
│  └────────────────┴────────────────┴──────────────────────────┘   │
│  ┌────────────────┬────────────────┬──────────────────────────┐   │
│  │ Sector Analysis│ Health Score   │  Screener Engine          │   │
│  │ • Rankings     │ • Composite    │  • 20+ Filters            │   │
│  │ • Bubble Charts│ • Grading      │  • Presets                │   │
│  │ • Distribution │ • Scoring      │  • CSV Export             │   │
│  └────────────────┴────────────────┴──────────────────────────┘   │
└────────────────────────────┬───────────────────────────────────────┘
                             │ Data Access
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    DATA ACCESS LAYER                               │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Database Utils (db.py)                           │ │
│  │  • Connection Management (Singleton)                         │ │
│  │  • Query Optimization                                       │ │
│  │  • Caching (600s TTL)                                       │ │
│  │  • Error Handling                                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Cache Layer (cache.py)                           │ │
│  │  • In-memory caching                                        │ │
│  │  • TTL management                                           │ │
│  │  • Cache invalidation                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬───────────────────────────────────────┘
                             │ SQL Queries
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              SQLite Database (n100.db)                        │ │
│  │  Size: 2.18 MB                                               │ │
│  │  Tables: 20                                                  │ │
│  │  Records: 10,000+                                            │ │
│  │                                                              │ │
│  │  Core Tables:                                                │ │
│  │  • companies (92)                                            │ │
│  │  • profit_loss (1,263)                                       │ │
│  │  • balance_sheet (1,225)                                     │ │
│  │  • cash_flow (1,164)                                         │ │
│  │  • financial_ratios (1,065)                                  │ │
│  │  • financial_kpis (1,164)                                    │ │
│  │  • peer_groups (56)                                          │ │
│  │  • sectors (9)                                               │ │
│  │  • stock_prices (5,520)                                      │ │
│  │  • market_cap (92)                                           │ │
│  │  • documents (1,585)                                         │ │
│  │  • annual_reports (1,533)                                    │ │
│  │  • valuation_summary (92)                                    │ │
│  │  • valuation_flags (92)                                      │ │
│  │  • financial_health_scores (92)                              │ │
│  │  • peer_benchmarks (13)                                      │ │
│  │  • sector_rankings (9)                                       │ │
│  │  • pros_cons (5)                                             │ │
│  │  • analysis (5)                                              │ │
│  │  • etl_audit (12)                                            │ │
│  │                                                              │ │
│  │  Indexes: Optimized for query performance                   │ │
│  │  Foreign Keys: Enabled                                       │ │
│  │  Journal Mode: WAL                                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬───────────────────────────────────────┘
                             │ ETL Pipeline
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Extract  │→│Normalize │→│Validate  │→│Transform │         │
│  │(12 Excel)│  │(Clean)   │  │(Quality) │  │(Rules)   │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
│                            │                                      │
│                            ▼                                      │
│                   ┌──────────────┐                                │
│                   │    Load      │                                │
│                   │  (Database)  │                                │
│                   └──────────────┘                                │
│                                                                   │
│  Modules:                                                        │
│  • extract.py: Excel file reading                                │
│  • normalizer.py: Data cleaning                                  │
│  • validator.py: Quality checks                                  │
│  • transform.py: Business rules                                  │
│  • load.py: Database loading                                     │
│  • pipeline.py: Orchestration                                    │
│  • data_quality.py: Quality reporting                            │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Excel Files (data/raw/)                          │ │
│  │                                                              │ │
│  │  • companies.xlsx (92 companies)                             │ │
│  │  • profit_loss.xlsx (1,263 records)                          │ │
│  │  • balance_sheet.xlsx (1,225 records)                        │ │
│  │  • cash_flow.xlsx (1,164 records)                            │ │
│  │  • ratios.xlsx (1,065 records)                               │ │
│  │  • stock_prices.xlsx (5,520 records)                         │ │
│  │  • market_cap.xlsx (92 records)                              │ │
│  │  • sectors.xlsx (92 records)                                 │ │
│  │  • peer_groups.xlsx (56 records)                             │ │
│  │  • documents.xlsx (1,585 records)                            │ │
│  │  • pros_cons.xlsx (5 records)                                │ │
│  │  • annual_reports.xlsx (1,533 records)                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Diagram

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Streamlit Dashboard                                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Page: Profile                                          ││
│  │  • Company Selector                                     ││
│  │  • Financial Statements                                 ││
│  │  • Ratios Display                                       ││
│  │  • Charts                                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
       │
       │ @st.cache_data (600s)
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Database Utils (db.py)                                      │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  def get_company_profile(company_id):                   ││
│  │      # Check cache                                      ││
│  │      # Query database                                   ││
│  │      # Return data                                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
       │
       │ SQL Queries
       ▼
┌─────────────────────────────────────────────────────────────┐
│  SQLite Database                                             │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │companies │profit_loss│balance_sheet│ratios  │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
└─────────────────────────────────────────────────────────────┘
       │
       │ Raw Data
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Analytics Engine                                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  KPI Calculator                                         ││
│  │  • Calculate ROE, ROCE, margins, etc.                   ││
│  │  • Validate ranges                                      ││
│  │  • Format output                                        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
       │
       │ KPIs
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Visualization Engine                                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Plotly Charts                                          ││
│  │  • Bar charts                                           ││
│  │  • Line charts                                          ││
│  │  • Radar charts                                         ││
│  │  • Treemaps                                             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
       │
       │ Charts
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Browser (User Interface)                                    │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Interactive Dashboard                                  ││
│  │  • Financial Statements                                 ││
│  │  • Ratio Tables                                         ││
│  │  • Charts                                               ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Additional Technical Details

### Error Handling

**Strategy**: Comprehensive exception handling with logging

**Levels**:
1. **Database Errors**: Connection failures, query errors
2. **Data Errors**: Missing data, invalid values
3. **Calculation Errors**: Division by zero, invalid operations
4. **UI Errors**: Rendering failures, state management

**Implementation**:
```python
try:
    # Operation
    result = perform_operation()
except SpecificException as e:
    logger.error(f"Specific error: {str(e)}")
    st.error("User-friendly message")
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}", exc_info=True)
    st.error("An unexpected error occurred")
```

### Logging Strategy

**Framework**: Python logging module

**Configuration**:
- **Log Level**: INFO (default), DEBUG (development)
- **Log Format**: Timestamp - Name - Level - Message
- **Handlers**: File + Console
- **Log Directory**: `logs/`

**Log Files**:
- `dashboard.log`: Dashboard operations
- `etl.log`: ETL pipeline
- `kpi.log`: KPI calculations
- `errors.log`: Error tracking

### Security

**Measures**:
- **SQL Injection**: Parameterized queries
- **Input Validation**: All inputs validated
- **Error Messages**: No sensitive data exposed
- **File Access**: Restricted to project directories
- **Database**: No external access

### Performance Optimization

**Techniques**:
1. **Database Indexing**: Optimized indexes on frequently queried columns
2. **Query Optimization**: Efficient SQL queries with JOINs
3. **Caching**: Multi-layer caching strategy
4. **Lazy Loading**: On-demand data retrieval
5. **Chunking**: Large dataset processing in chunks
6. **Connection Pooling**: Singleton connection pattern

### Scalability

**Current Capacity**:
- **Companies**: 92 (Nifty 100)
- **Records**: 10,000+
- **Users**: Single user (local deployment)
- **Data Size**: 2.18 MB

**Scalability Path**:
- **Database**: Migration to PostgreSQL/MySQL for multi-user
- **Caching**: Redis for distributed caching
- **Deployment**: Docker containers for cloud deployment
- **API**: REST API for external integrations

---

**End of Architecture Documentation**

For user guide, see [User_Guide.md](User_Guide.md)  
For project overview, see [Project_Summary.md](Project_Summary.md)  
For sprint details, see [Sprint4_Retrospective.md](Sprint4_Retrospective.md)