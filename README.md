# N100 Financial Intelligence Platform

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.28%2B-red)
![SQLite](https://img.shields.io/badge/sqlite-3.25%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)
![Status](https://img.shields.io/badge/status-production_ready-success)

A production-grade financial intelligence platform for comprehensive analysis of Nifty 100 companies. This platform combines automated ETL pipelines, advanced financial analytics, peer comparison engines, and an interactive Streamlit dashboard to provide actionable investment insights.

## Table of Contents

- [Problem Statement](#problem-statement)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Requirements](#requirements)
- [How to Run](#how-to-run)
- [ETL Pipeline](#etl-pipeline)
- [Dashboard](#dashboard)
- [Example Screenshots](#example-screenshots)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Problem Statement

Financial analysts and investors face significant challenges when analyzing Nifty 100 companies:

1. **Data Fragmentation**: Financial data scattered across multiple Excel files with inconsistent formats
2. **Manual Calculations**: Time-consuming manual calculation of 30+ financial KPIs and ratios
3. **Peer Comparison Difficulty**: Lack of standardized peer group benchmarking tools
4. **Limited Historical Analysis**: Difficulty tracking multi-year trends and sector performance
5. **Valuation Complexity**: No integrated valuation framework with flagging mechanisms
6. **Report Generation**: Manual report creation and data export processes

The N100 Financial Intelligence Platform solves these problems by providing:

- Automated ETL pipeline for 12 financial datasets
- 30+ calculated financial KPIs and ratios
- Peer comparison engine with radar charts
- Sector analysis and trend tracking
- Automated valuation with Excel exports
- Interactive dashboard with 8 specialized pages
- CSV/Excel export capabilities

## Features

### Core Analytics Engine

- **Financial Ratio Engine**: 30+ KPIs across profitability, liquidity, leverage, efficiency, and valuation
- **Peer Comparison Engine**: Automatic peer group assignment and benchmarking
- **Radar Charts**: Multi-dimensional company comparison visualization
- **Screener Engine**: Advanced filtering with 94+ companies across 9 sectors
- **Valuation Module**: Automated P/E, P/B, EV/EBITDA calculations with flagging
- **Health Score Engine**: Composite financial health scoring system

### Dashboard Modules

1. **Home Dashboard**: KPI overview, market summary, quick company search
2. **Company Profile**: Detailed financial statements, ratios, and metrics
3. **Stock Screener**: Filter companies by 20+ financial criteria
4. **Peer Comparison**: Side-by-side analysis with radar charts
5. **Trend Analysis**: 12-year historical performance tracking
6. **Sector Analysis**: Sector-wise performance and distribution analysis
7. **Capital Allocation**: Cash flow analysis and capital structure visualization
8. **Annual Reports**: Comprehensive financial report generation

### Data Management

- **ETL Pipeline**: Automated extraction, transformation, and loading
- **Data Validation**: Comprehensive quality checks and validation reports
- **Database**: SQLite with 20+ tables and proper indexing
- **Caching**: 10-minute cache TTL for optimal performance
- **Export**: CSV and Excel export functionality

## Technology Stack

### Backend

- **Language**: Python 3.8+
- **Database**: SQLite 3.25+
- **Data Processing**: Pandas 2.0+, NumPy 1.24+
- **ETL**: Custom pipeline with validation and normalization

### Frontend

- **Framework**: Streamlit 1.28+
- **Visualization**: Plotly 5.17+
- **Charts**: Interactive bar, line, radar, treemap, waterfall, heatmap, gauge charts

### Analytics

- **KPI Engine**: Custom financial ratio calculator
- **Peer Analysis**: Benchmarking and percentile calculations
- **Valuation**: Automated valuation with Excel export
- **Health Score**: Composite scoring system

### Development

- **Testing**: pytest, unittest
- **Logging**: Comprehensive logging framework
- **Configuration**: Centralized settings management
- **Documentation**: Markdown-based documentation

## Project Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Dashboard                       │
│                    (8 Specialized Pages)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Analytics Layer                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ KPI Engine   │ Peer Engine  │ Valuation    │ Health Score │  │
│  │ (30+ KPIs)   │ (13 Groups)  │ (92 Records) │ (Composite)  │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Layer (SQLite)                       │
│  ┌────────┬────────┬────────┬────────┬────────┬────────┐        │
│  │Companies│Ratios  │ KPIs   │ Peers  │Sectors │Reports │        │
│  │  (92)  │(1,065) │(1,164) │  (56)  │  (9)   │(1,585) │        │
│  └────────┴────────┴────────┴────────┴────────┴────────┘        │
│  Total: 20 Tables, 10,000+ Records, 2.18 MB                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ETL Pipeline                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Extract  │→│Normalize │→│Validate  │→│Transform │        │
│  │(12 Excel)│  │(Clean)   │  │(Quality) │  │(Rules)   │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                            │                                     │
│                            ▼                                     │
│                   ┌──────────────┐                               │
│                   │    Load      │                               │
│                   │  (Database)  │                               │
│                   └──────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Sources                                  │
│         (12 Excel Files in data/raw/)                            │
│  • companies.xlsx • profit_loss.xlsx • balance_sheet.xlsx       │
│  • cash_flow.xlsx • ratios.xlsx • stock_prices.xlsx            │
│  • market_cap.xlsx • sectors.xlsx • peer_groups.xlsx           │
│  • documents.xlsx • pros_cons.xlsx • annual_reports.xlsx       │
└─────────────────────────────────────────────────────────────────┘
```

## Folder Structure

```
N100_Financial_Intelligence_Platform/
├── data/
│   ├── database/                    # SQLite database storage
│   │   └── n100.db                 # Main database (2.18 MB, 20 tables)
│   └── raw/                         # Raw Excel files (12 datasets)
│       ├── companies.xlsx
│       ├── profit_loss.xlsx
│       ├── balance_sheet.xlsx
│       ├── cash_flow.xlsx
│       ├── ratios.xlsx
│       ├── stock_prices.xlsx
│       ├── market_cap.xlsx
│       ├── sectors.xlsx
│       ├── peer_groups.xlsx
│       ├── documents.xlsx
│       ├── pros_cons.xlsx
│       └── annual_reports.xlsx
│
├── docs/                            # Documentation
│   ├── User_Guide.md                # User documentation
│   ├── Architecture.md              # Technical architecture
│   ├── Project_Summary.md           # Project overview
│   ├── Sprint4_Retrospective.md     # Sprint retrospective
│   ├── screenshots/                 # Dashboard screenshots
│   ├── manual_data_review.md
│   ├── etl_validation_summary.md
│   └── SPRINT1_REVIEW.md
│
├── logs/                            # Application logs
│   └── dashboard.log
│
├── notebooks/                       # SQL queries and analysis
│   └── exploratory_queries.sql
│
├── output/                          # Generated outputs
│   ├── valuation_summary.xlsx       # Valuation Excel report
│   ├── valuation_flags.csv          # Valuation flags
│   ├── financial_health_scores.csv  # Health scores
│   ├── peer_percentiles.csv         # Peer benchmarks
│   ├── peer_reports/                # Peer comparison reports
│   └── radar_charts/                # Radar chart visualizations
│
├── pages/                           # Dashboard pages
│   ├── 01_home.py                   # Home dashboard
│   ├── 02_profile.py                # Company profile
│   ├── 03_screener.py               # Stock screener
│   ├── 04_peers.py                  # Peer comparison
│   ├── 05_trends.py                 # Trend analysis
│   ├── 06_sectors.py                # Sector analysis
│   ├── 07_capital.py                # Capital allocation
│   └── 08_reports.py                # Annual reports
│
├── reports/                         # Generated reports
│   └── data_quality_report_*.html   # Data quality reports
│
├── src/                             # Source code
│   ├── config/                      # Configuration
│   │   ├── column_mappings.py
│   │   ├── constants.py
│   │   ├── logging_config.py
│   │   └── settings.py
│   ├── database/                    # Database operations
│   │   ├── connection.py
│   │   ├── models.py
│   │   ├── schema.py
│   │   └── seed.py
│   ├── etl/                         # ETL pipeline
│   │   ├── extract.py
│   │   ├── normalizer.py
│   │   ├── validator.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   ├── pipeline.py
│   │   └── data_quality.py
│   ├── kpi_engine/                  # KPI calculations
│   │   ├── calculator.py
│   │   ├── profitability.py
│   │   ├── liquidity.py
│   │   ├── leverage.py
│   │   ├── efficiency.py
│   │   ├── valuation.py
│   │   ├── cashflow.py
│   │   ├── growth.py
│   │   ├── validator.py
│   │   └── formatter.py
│   ├── analytics/                   # Advanced analytics
│   │   ├── valuation.py
│   │   ├── peer.py
│   │   ├── radar.py
│   │   ├── trends.py
│   │   ├── sector.py
│   │   └── ratio_engine.py
│   ├── screener/                    # Stock screener
│   │   ├── engine.py
│   │   ├── filters.py
│   │   ├── exporter.py
│   │   └── presets.py
│   ├── peer_analysis/               # Peer comparison
│   │   ├── benchmarking.py
│   │   ├── comparison.py
│   │   ├── percentile.py
│   │   └── radar.py
│   ├── sector_analysis/             # Sector analysis
│   │   ├── sector_summary.py
│   │   ├── rankings.py
│   │   └── visualization.py
│   ├── health_score/                # Health scoring
│   │   ├── engine.py
│   │   ├── scoring.py
│   │   ├── grading.py
│   │   └── rules.py
│   ├── reports/                     # Report generation
│   │   ├── company_report.py
│   │   ├── excel_export.py
│   │   ├── pdf_export.py
│   │   └── sector_report.py
│   ├── visualization/               # Chart utilities
│   │   ├── bar.py
│   │   ├── line.py
│   │   ├── radar.py
│   │   ├── treemap.py
│   │   ├── waterfall.py
│   │   ├── heatmap.py
│   │   └── gauges.py
│   ├── alerts/                      # Alert system
│   │   ├── alerts.py
│   │   ├── rules.py
│   │   ├── watchlist.py
│   │   └── notification.py
│   ├── utils/                       # Utilities
│   │   ├── cache.py
│   │   ├── formatter.py
│   │   ├── helpers.py
│   │   ├── logger.py
│   │   └── parser.py
│   ├── dashboard/                   # Dashboard framework
│   │   ├── app.py                   # Main application
│   │   ├── utils.py
│   │   ├── components/
│   │   ├── pages/
│   │   └── utils/
│   └── tests/                       # Unit tests
│       ├── test_etl.py
│       ├── test_database.py
│       ├── test_kpi.py
│       └── test_dashboard.py
│
├── .gitignore
├── README.md                        # This file
├── requirements.txt                 # Python dependencies
├── requirements-dashboard.txt       # Dashboard dependencies
├── run_etl.py                       # ETL pipeline runner
├── populate_financial_kpis.py       # KPI calculator
└── MODULE_*_COMPLETION_REPORT.md    # Sprint completion reports
```

## Installation

### Prerequisites

- **Python**: 3.8 or higher (3.11+ recommended)
- **pip**: Package manager
- **SQLite**: 3.25 or higher (included with Python)
- **Git**: For cloning the repository

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/santanumaity3155-spec/N100_Financial_Intelligence_Platform.git
   cd N100_Financial_Intelligence_Platform
   ```

2. **Create virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dashboard.txt
   ```

   **Core dependencies:**
   - pandas >= 2.0.0
   - numpy >= 1.24.0
   - openpyxl >= 3.1.0
   - sqlalchemy >= 2.0.0
   - streamlit >= 1.28.0
   - plotly >= 5.17.0
   - python-dotenv >= 1.0.0

4. **Prepare data**
   - Place 12 Excel files in `data/raw/` directory
   - Ensure files follow the standard N100 data format
   - Run ETL pipeline to initialize database

## Requirements

### Python Version

- **Minimum**: Python 3.8
- **Recommended**: Python 3.11+
- **Tested On**: Python 3.11

### Dependencies

See `requirements.txt` and `requirements-dashboard.txt` for complete lists.

**Key Dependencies:**
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **openpyxl**: Excel file reading/writing
- **sqlalchemy**: Database ORM
- **streamlit**: Dashboard framework
- **plotly**: Interactive visualizations
- **python-dotenv**: Environment configuration

### Database

- **Type**: SQLite
- **Version**: 3.25+
- **Location**: `data/database/n100.db`
- **Size**: ~2.18 MB
- **Tables**: 20
- **Records**: 10,000+
- **Indexes**: Optimized for query performance

## How to Run

### 1. Initialize Database (First Time Only)

Run the ETL pipeline to extract data from Excel files and populate the database:

```bash
python run_etl.py
```

This will:
- Extract data from 12 Excel files
- Normalize and clean data
- Validate data quality
- Transform data according to business rules
- Load into SQLite database
- Generate quality reports

**Expected Output:**
- Database created at `data/database/n100.db`
- Quality reports in `reports/`
- Load audit in `output/`

### 2. Calculate Financial KPIs

After ETL completes, calculate financial KPIs:

```bash
python populate_financial_kpis.py
```

**Expected Output:**
- 1,164+ KPI records in database
- Financial health scores in `output/financial_health_scores.csv`

### 3. Launch Dashboard

Start the Streamlit dashboard:

```bash
streamlit run src/dashboard/app.py
```

The dashboard will open in your default browser at `http://localhost:8501`

### 4. Navigate Dashboard

Use the sidebar to navigate between 8 specialized pages:
1. 🏠 Home - Dashboard overview
2. 👤 Profile - Company profiles
3. 🔍 Screener - Stock screening
4. 👥 Peers - Peer comparison
5. 📈 Trends - Trend analysis
6. 🏭 Sectors - Sector analysis
7. 💰 Capital - Capital allocation
8. 📑 Reports - Annual reports

## ETL Pipeline

### Pipeline Overview

The ETL pipeline processes 12 Excel files through 5 stages:

```
Excel Files → Extract → Normalize → Validate → Transform → Load → Database
```

### Stage 1: Extraction

**Module**: `src/etl/extract.py`

**Functionality**:
- Reads Excel files from `data/raw/`
- Handles multiple sheet formats
- Validates file existence and structure
- Extracts data into pandas DataFrames

**Input**: 12 Excel files
**Output**: Raw DataFrames

### Stage 2: Normalization

**Module**: `src/etl/normalizer.py`

**Functionality**:
- Standardizes company IDs (uppercase, removes special characters)
- Normalizes year formats (FY2024 → 2024-FY)
- Cleans numeric columns (removes commas, handles negatives)
- Removes duplicate records based on business keys

**Input**: Raw DataFrames
**Output**: Cleaned DataFrames

### Stage 3: Validation

**Module**: `src/etl/validator.py`

**Functionality**:
- Checks required columns exist
- Detects missing values with dataset-specific thresholds
- Identifies duplicate records
- Validates data types
- Generates validation reports in HTML/JSON

**Input**: Cleaned DataFrames
**Output**: Validation reports, validated DataFrames

### Stage 4: Transformation

**Module**: `src/etl/transform.py`

**Functionality**:
- Applies business rules
- Calculates derived metrics
- Ensures data consistency
- Prepares data for loading

**Input**: Validated DataFrames
**Output**: Transformed DataFrames

### Stage 5: Loading

**Module**: `src/etl/load.py`

**Functionality**:
- Creates database tables with proper schema
- Loads data with chunking for large datasets
- Handles foreign key constraints
- Verifies row counts
- Generates load audit reports

**Input**: Transformed DataFrames
**Output**: SQLite database, load audit reports

### Running the Pipeline

```bash
# Run complete pipeline
python run_etl.py

# Monitor progress in console output
# Check reports in reports/ directory
# Verify database in data/database/n100.db
```

## Dashboard

### Dashboard Architecture

The dashboard is built with Streamlit and consists of:

- **Main Application**: `src/dashboard/app.py` - Entry point and navigation
- **8 Specialized Pages**: Located in `pages/` directory
- **Database Utils**: `src/dashboard/utils/db.py` - Data access layer
- **Components**: Reusable UI components
- **Caching**: 10-minute TTL for optimal performance

### Dashboard Pages

#### 1. Home Dashboard (`pages/01_home.py`)

**Features**:
- Market overview with key metrics
- Quick company search
- Recent updates and alerts
- Navigation guide

**Data Sources**: companies, financial_kpis, market_cap

#### 2. Company Profile (`pages/02_profile.py`)

**Features**:
- Detailed financial statements (P&L, Balance Sheet, Cash Flow)
- 30+ financial ratios and KPIs
- Historical performance charts
- Peer comparison summary

**Data Sources**: profit_loss, balance_sheet, cash_flow, financial_ratios, financial_kpis

#### 3. Stock Screener (`pages/03_screener.py`)

**Features**:
- Filter by 20+ financial criteria
- Pre-built screening presets
- Sortable results table
- CSV export functionality

**Data Sources**: financial_ratios, financial_kpis, companies

#### 4. Peer Comparison (`pages/04_peers.py`)

**Features**:
- Automatic peer group assignment
- Radar chart comparison
- Benchmark percentile rankings
- Side-by-side metrics

**Data Sources**: peer_groups, financial_ratios, financial_kpis

#### 5. Trend Analysis (`pages/05_trends.py`)

**Features**:
- 12-year historical trends
- Multi-metric line charts
- Growth rate analysis
- CAGR calculations

**Data Sources**: financial_kpis, profit_loss, balance_sheet, cash_flow

#### 6. Sector Analysis (`pages/06_sectors.py`)

**Features**:
- Sector-wise performance comparison
- Bubble charts for market cap vs returns
- Sector distribution analysis
- Top performers ranking

**Data Sources**: sectors, financial_ratios, market_cap

#### 7. Capital Allocation (`pages/07_capital.py`)

**Features**:
- Cash flow analysis (Operating, Investing, Financing)
- Treemap visualization
- Capital structure metrics
- Dividend and buyback analysis

**Data Sources**: cash_flow, balance_sheet

#### 8. Annual Reports (`pages/08_reports.py`)

**Features**:
- Comprehensive financial reports
- Search and filter functionality
- Report generation
- Export to CSV/Excel

**Data Sources**: documents, profit_loss, balance_sheet, cash_flow, ratios

### Example Commands

```bash
# Launch dashboard
streamlit run src/dashboard/app.py

# Run with custom port
streamlit run src/dashboard/app.py --server.port 8502

# Run with custom theme
streamlit run src/dashboard/app.py --theme.base dark

# Run in headless mode
streamlit run src/dashboard/app.py --server.headless true
```

## Example Screenshots

### Home Dashboard

![Home Dashboard](docs/screenshots/01_home.png)

**Description**: The home dashboard provides an overview of the N100 Financial Intelligence Platform. It displays:
- Welcome message and platform introduction
- Key performance indicators (KPIs) for the platform
- Quick company search functionality
- Navigation guide to all 8 dashboard pages
- Database connection status
- Application version and module information

**Key Features**:
- Market summary metrics
- Quick access to company search
- Visual navigation guide
- Real-time database status

### Company Profile

![Company Profile](docs/screenshots/02_profile.png)

**Description**: The company profile page provides comprehensive financial analysis for selected companies. It displays:
- Company information and sector classification
- Profit & Loss statement with revenue, expenses, and profit metrics
- Balance sheet with assets, liabilities, and equity
- Cash flow statement (Operating, Investing, Financing)
- 30+ financial ratios and KPIs
- Historical performance charts
- Peer comparison summary

**Key Features**:
- Multi-year financial statements
- Interactive charts for trend visualization
- Comprehensive ratio analysis
- Export capabilities

### Stock Screener

![Stock Screener](docs/screenshots/03_screener.png)

**Description**: The stock screener allows users to filter and screen Nifty 100 companies based on financial criteria. It displays:
- Filter panel with 20+ financial criteria
- Real-time filtering results
- Sortable results table with 94+ companies
- Pre-built screening presets (Value, Growth, Quality, Dividend)
- CSV export functionality
- Column visibility toggles

**Key Features**:
- Multi-criteria filtering
- Pre-built screening strategies
- Real-time results update
- Export to CSV

### Peer Comparison

![Peer Comparison](docs/screenshots/04_peers.png)

**Description**: The peer comparison page enables benchmarking against industry peers. It displays:
- Company selection and peer group assignment
- Radar chart for multi-dimensional comparison
- Side-by-side metrics table
- Percentile rankings
- Benchmark analysis

**Key Features**:
- 13 peer groups across sectors
- Interactive radar charts
- Comprehensive metrics comparison
- Visual benchmarking

### Trend Analysis

![Trend Analysis](docs/screenshots/05_trends.png)

**Description**: The trend analysis page shows historical performance over 12 years. It displays:
- Multi-metric line charts
- Year-over-year growth rates
- CAGR calculations
- Historical KPI trends
- Comparative analysis

**Key Features**:
- 12 years of historical data
- Multiple metric selection
- Interactive zoom and pan
- Growth rate calculations

### Sector Analysis

![Sector Analysis](docs/screenshots/06_sectors.png)

**Description**: The sector analysis page provides sector-wide performance metrics. It displays:
- Sector-wise performance comparison
- Bubble charts (Market Cap vs Returns)
- Sector distribution analysis
- Top performers ranking
- Sector rotation indicators

**Key Features**:
- 9 sector classifications
- Interactive bubble charts
- Sector benchmarking
- Performance ranking

### Capital Allocation

![Capital Allocation](docs/screenshots/07_capital.png)

**Description**: The capital allocation page analyzes cash flow and capital structure. It displays:
- Cash flow statement (Operating, Investing, Financing)
- Treemap visualization of cash flow allocation
- Capital structure metrics (Debt/Equity)
- Dividend and buyback analysis
- Free cash flow trends

**Key Features**:
- Cash flow breakdown
- Interactive treemap
- Capital structure analysis
- Shareholder return analysis

### Annual Reports

![Annual Reports](docs/screenshots/08_reports.png)

**Description**: The annual reports page generates comprehensive financial reports. It displays:
- Company search and selection
- Comprehensive financial report generation
- Report sections (Overview, P&L, Balance Sheet, Cash Flow, Ratios)
- Search and filter functionality
- Export to CSV/Excel

**Key Features**:
- Automated report generation
- Multi-section reports
- Search and filter
- Export capabilities

## Future Improvements

### Planned Features

1. **Enhanced Visualization**
   - Candlestick charts for stock prices
   - Correlation matrices
   - Monte Carlo simulations
   - Scenario analysis

2. **Advanced Analytics**
   - Machine learning predictions
   - Sentiment analysis integration
   - Alternative data sources
   - Portfolio optimization

3. **User Experience**
   - Customizable dashboard layouts
   - Saved filters and preferences
   - Collaborative features
   - Mobile-responsive design

4. **Data Expansion**
   - Real-time data feeds
   - Global market coverage
   - ESG metrics integration
   - Analyst estimates

5. **Performance**
   - Database query optimization
   - Advanced caching strategies
   - Parallel processing
   - Cloud deployment support

## Contributors

**Development Team**: Bluestock Financial Intelligence Platform Team

**Sprint Completion**:
- ✅ Sprint 1 - Data Foundation
- ✅ Sprint 2 - Financial Ratio Engine
- ✅ Sprint 3 - Screener Engine, Peer Engine, Radar Charts
- ✅ Sprint 4 - Complete Dashboard and Analytics

## License

MIT License - See LICENSE file for details

## Acknowledgements

- **Data Source**: Nifty 100 companies financial data
- **Framework**: Streamlit for dashboard framework
- **Visualization**: Plotly for interactive charts
- **Database**: SQLite for data storage
- **Analytics**: Pandas and NumPy for data processing

---

**Last Updated**: August 6, 2026  
**Version**: 1.0.0  
**Sprint**: 4 - Module 7 (Complete)  
**Status**: Production Ready  
**Platform**: N100 Financial Intelligence Platform  
**Organization**: Bluestock