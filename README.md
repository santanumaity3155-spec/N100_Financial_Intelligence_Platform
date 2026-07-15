# N100 Financial Intelligence Platform

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![SQLite](https://img.shields.io/badge/sqlite-3.25%2B-green)
![License](https://img.shields.io/badge/license-MIT-orange)

A production-grade ETL pipeline and financial intelligence platform for analyzing Nifty 100 companies. This platform extracts financial data from Excel files, transforms it through a robust ETL pipeline, and loads it into a SQLite database for comprehensive financial analysis and KPI calculations.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [ETL Workflow](#etl-workflow)
- [Testing](#testing)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [Sprint 1 Completion](#sprint-1-completion)

## Features

### Core Functionality
- **Automated ETL Pipeline**: Extract, transform, and load financial data from Excel files
- **Data Validation**: Comprehensive validation with missing value detection and duplicate checking
- **Data Normalization**: Standardize company IDs, years, and financial metrics
- **KPI Calculations**: 30+ financial KPIs including profitability, liquidity, leverage, and efficiency ratios
- **Database Management**: SQLite database with proper schema design and indexing
- **Quality Reports**: Automated data quality reporting in HTML and JSON formats

### Financial Analysis
- **Profit & Loss Analysis**: Revenue, expenses, profit margins, and growth metrics
- **Balance Sheet Analysis**: Assets, liabilities, equity, and financial position
- **Cash Flow Analysis**: Operating, investing, and financing cash flows
- **Valuation Metrics**: P/E ratio, P/B ratio, market cap, and enterprise value
- **Peer Group Analysis**: Benchmarking against industry peers
- **Sector Analysis**: Sector-wise performance and distribution

## Architecture

```
┌─────────────────┐
│   Excel Files   │ (Raw Data)
│  (data/raw/)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Extraction    │ (src/etl/extract.py)
│  (DataExtractor)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Normalization  │ (src/etl/normalizer.py)
│ (DataNormalizer)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Validation    │ (src/etl/validator.py)
│ (DataValidator) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Transformation  │ (src/etl/transform.py)
│(DataTransformer)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     Loading     │ (src/etl/load.py)
│  (DataLoader)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   SQLite DB     │ (data/database/n100.db)
│  (14 Tables)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  KPI Engine     │ (src/kpi_engine/)
│  (30+ KPIs)     │
└─────────────────┘
```

## Folder Structure

```
N100_Financial_Intelligence_Platform/
├── data/
│   ├── database/              # SQLite database storage
│   │   └── n100.db           # Main database file
│   └── raw/                   # Raw Excel files (12 datasets)
│       ├── companies.xlsx
│       ├── profit_loss.xlsx
│       ├── balance_sheet.xlsx
│       ├── cash_flow.xlsx
│       └── ... (8 more datasets)
│
├── docs/                      # Documentation
│   ├── manual_data_review.md
│   ├── etl_validation_summary.md
│   └── [Sprint 1 review docs]
│
├── logs/                      # Application logs
│
├── notebooks/                 # SQL queries and analysis
│   └── exploratory_queries.sql
│
├── reports/                   # Generated reports
│   ├── data_quality_report_*.html
│   ├── data_quality_report_*.json
│   ├── load_audit.csv
│   └── validation_failures.csv
│
├── src/                       # Source code
│   ├── config/                # Configuration
│   │   └── column_mappings.py
│   ├── database/              # Database operations
│   │   ├── connection.py
│   │   └── schema.py
│   ├── etl/                   # ETL pipeline modules
│   │   ├── extract.py
│   │   ├── normalizer.py
│   │   ├── validator.py
│   │   ├── transform.py
│   │   ├── load.py
│   │   ├── pipeline.py
│   │   └── data_quality.py
│   ├── kpi_engine/            # KPI calculations
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
│   ├── tests/                 # Unit tests
│   │   ├── test_etl.py
│   │   ├── test_etl_comprehensive.py
│   │   ├── test_database.py
│   │   ├── test_kpi.py
│   │   └── ... (more tests)
│   └── [other modules]
│
├── .gitignore
├── README.md                  # This file
├── run_etl.py                 # ETL pipeline runner
└── populate_financial_kpis.py # KPI calculator script
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- SQLite 3.25 or higher (usually included with Python)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd N100_Financial_Intelligence_Platform
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   **Required packages:**
   - pandas
   - openpyxl
   - numpy
   - sqlalchemy

4. **Prepare data**
   - Place Excel files in `data/raw/` directory
   - Ensure all 12 required datasets are present

## Usage

### Running the ETL Pipeline

Execute the complete ETL pipeline:

```bash
python run_etl.py
```

This will:
1. Extract data from Excel files
2. Normalize and clean data
3. Validate data quality
4. Transform data
5. Load into SQLite database
6. Generate quality reports

### Running KPI Calculations

After ETL pipeline completes, calculate financial KPIs:

```bash
python populate_financial_kpis.py
```

### Running Tests

Execute the test suite:

```bash
# Run all tests
python -m pytest src/tests/ -v

# Run specific test file
python -m pytest src/tests/test_etl_comprehensive.py -v

# Run with unittest
python -m unittest discover src/tests -v
```

### Exploratory Data Analysis

Run exploratory SQL queries:

```bash
# Using SQLite CLI
sqlite3 data/database/n100.db < notebooks/exploratory_queries.sql

# Or open in SQLite browser
sqlite3 data/database/n100.db
```

## Database Schema

### Core Tables

| Table | Records | Description |
|-------|---------|-------------|
| companies | 92 | Company master data |
| profit_loss | 1,263 | Profit & Loss statements |
| balance_sheet | 1,225 | Balance sheet data |
| cash_flow | 1,164 | Cash flow statements |
| sectors | 92 | Sector classifications |
| stock_prices | 5,520 | Historical stock prices |
| market_cap | 92 | Market capitalization |
| financial_ratios | 1,065 | Financial ratios |
| financial_kpis | 1,164 | Calculated KPIs |
| peer_groups | 56 | Peer group assignments |
| analysis | 5 | Analysis data |
| documents | 1,585 | Document references |
| pros_cons | 5 | Pros and cons analysis |

### Key Relationships

```
companies (1) ──────┬── (n) profit_loss
                    ├── (n) balance_sheet
                    ├── (n) cash_flow
                    ├── (n) sectors
                    ├── (n) stock_prices
                    ├── (n) market_cap
                    ├── (n) financial_ratios
                    ├── (n) financial_kpis
                    └── (n) peer_groups
```

## ETL Workflow

### 1. Extraction
- Reads Excel files from `data/raw/`
- Handles multiple sheet formats
- Validates file existence and structure

### 2. Normalization
- Standardizes company IDs (uppercase, removes special chars)
- Normalizes year formats (FY2024 → 2024-FY)
- Cleans numeric columns (removes commas, handles negatives)
- Removes duplicate records based on business keys

### 3. Validation
- Checks required columns exist
- Detects missing values with dataset-specific thresholds
- Identifies duplicate records
- Validates data types
- Generates validation reports

### 4. Transformation
- Applies business rules
- Calculates derived metrics
- Ensures data consistency

### 5. Loading
- Creates database tables with proper schema
- Loads data with chunking for large datasets
- Handles foreign key constraints
- Verifies row counts
- Generates load audit reports

## Testing

### Test Coverage

The project includes comprehensive tests covering:

- **DataLoader**: Table loading, verification, statistics
- **DataValidator**: Column validation, missing values, duplicates, data types
- **DataNormalizer**: Company ID normalization, year normalization, duplicate removal
- **Database Operations**: Foreign keys, orphaned records, duplicates
- **Edge Cases**: Empty DataFrames, None values, special characters, large datasets

### Running Tests

```bash
# Run all tests
python -m pytest src/tests/ -v --tb=short

# Run with coverage
python -m pytest src/tests/ --cov=src --cov-report=html
```

## Documentation

### Available Documentation

- **README.md**: This file - project overview and quick start
- **Database Schema**: See "Database Schema" section above
- **ETL Workflow**: See "ETL Workflow" section above
- **Exploratory Queries**: `notebooks/exploratory_queries.sql`
- **Manual Data Review**: `docs/manual_data_review.md`
- **ETL Validation Summary**: `docs/etl_validation_summary.md`
- **Sprint 1 Review**: `docs/SPRINT1_REVIEW.md`

### API Documentation

Detailed API documentation is available in the source code docstrings. Key classes:

- `DataExtractor`: Excel file extraction
- `DataNormalizer`: Data cleaning and normalization
- `DataValidator`: Data quality validation
- `DataTransformer`: Data transformation
- `DataLoader`: Database loading
- `ETLPipeline`: Pipeline orchestration

## Troubleshooting

### Common Issues

#### 1. Database Locked Error
**Solution**: Ensure no other connections are open to the database
```python
# Close all connections
from src.database.connection import close_connection
close_connection()
```

#### 2. Missing Excel Files
**Solution**: Verify all 12 Excel files are in `data/raw/` directory
```bash
ls data/raw/*.xlsx
```

#### 3. Foreign Key Violations
**Solution**: The ETL pipeline disables foreign key checks during loading. Run validation after loading:
```sql
PRAGMA foreign_key_check;
```

#### 4. Memory Issues with Large Datasets
**Solution**: Adjust chunk size in DataLoader
```python
loader.load_table('table_name', df, chunksize=1000)
```

#### 5. Column Name Mismatches
**Solution**: The loader automatically sanitizes column names. Check logs for details.

### Logging

Logs are stored in the `logs/` directory. Adjust log level in configuration:

```python
from src.config.logging_config import get_logger
logger = get_logger(__name__)
logger.setLevel('DEBUG')  # For detailed logging
```

## Sprint 1 Completion

### Completed Features

✅ **Environment Setup**: Python environment, dependencies, project structure
✅ **ETL Pipeline**: Complete extraction, normalization, validation, transformation, and loading
✅ **Excel Extraction**: All 12 datasets successfully extracted
✅ **Data Normalization**: Company IDs, years, and numeric columns normalized
✅ **Data Transformation**: Business rules and calculations applied
✅ **Database Schema**: 14 tables created with proper relationships and indexes
✅ **Database Loading**: All 12 datasets loaded (5,520+ companies records)
✅ **Validation Reports**: Automated quality reports generated
✅ **Load Audit**: Complete audit trail maintained
✅ **Exploratory Queries**: 20 professional SQL queries for analysis
✅ **Manual Data Review**: 5 companies reviewed with detailed analysis
✅ **ETL Validation**: Exit criteria verified and satisfied
✅ **Unit Tests**: 35+ comprehensive tests covering all ETL components
✅ **Documentation**: Complete README, schema docs, and workflow guides
✅ **Sprint Review**: Comprehensive review document generated

### Sprint 1 Statistics

- **Total Companies**: 92
- **Total Tables**: 14
- **Total Records**: 10,000+
- **Test Coverage**: 35+ tests
- **Documentation Files**: 5+
- **Validation Checks**: 6 categories
- **KPI Calculations**: 30+ metrics

### Exit Criteria Status

| Criteria | Status |
|----------|--------|
| Companies count > 0 | ✅ PASS |
| No foreign key violations | ✅ PASS |
| Load audit exists and successful | ✅ PASS |
| Validation report exists | ✅ PASS |
| All tables exist with data | ✅ PASS |
| No critical data integrity issues | ✅ PASS |

**Sprint 1 Status: ✅ COMPLETE AND READY FOR SUBMISSION**

## Contributing

This is a Sprint 1 deliverable. For Sprint 2 enhancements, please refer to the project roadmap.

## License

MIT License - See LICENSE file for details

## Contact

For questions or issues, please contact the development team.

---

**Last Updated**: 2025-07-15
**Version**: 1.0.0
**Sprint**: 1